"""Recommendation Pipeline Orchestrator — connects LLM, SQL Filter, and ILP Solver."""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.constraints import ExtractedConstraints
from app.schemas.recommendation import (
    ChatRequest, ChatResponse, RecommendationResult, RecommendedItem
)
from app.services.intent_classifier import classify_intent
from app.services.constraint_extractor import extract_constraints
from app.services.constraint_merger import merge_constraints
from app.services.menu_filter import filter_menu_items
from app.services.optimizer import optimize_menu
from app.services.explanation_generator import generate_explanation, generate_question_answer
from app.models.restaurant import Restaurant
from app.models.conversation import Conversation
from sqlalchemy import select
import uuid
from datetime import datetime

async def process_chat_request(request: ChatRequest, db: AsyncSession, user_id: str) -> ChatResponse:
    """
    Full recommendation pipeline:
      0.5 Intent Classification (Guardrail)
      1. Extract constraints from user message (LLM Delta)
      1.5 Merge delta into existing conversation state (Python Deterministic)
      2. Filter menu items from database (SQL)
      3. Optimize meal combination (ILP Solver)
      4. Generate grounded explanation (LLM)
    """
    import asyncio
    
    # --- Step 0: Conversation State Management ---
    conversation = None
    conversation_history = []
    existing_constraints = {}
    
    if request.conversation_id:
        conversation = await db.get(Conversation, str(request.conversation_id))
        if conversation:
            conversation_history = conversation.messages
            existing_constraints = conversation.current_constraints
            
    if not conversation:
        conversation = Conversation(
            restaurant_id=str(request.restaurant_id),
            user_id=user_id,
            messages=[],
            current_constraints={},
            current_cart=[]
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

    # --- Step 0.5 & 1: Parallel Intent Classification and Constraint Extraction ---
    intent_result, delta_constraints = await asyncio.gather(
        classify_intent(request.message),
        extract_constraints(
            request.message, 
            conversation_history=conversation_history, 
            existing_constraints=existing_constraints,
            current_cart=conversation.current_cart
        )
    )

    if intent_result.intent in ["OFF_TOPIC", "ADVERSARIAL", "GREETING", "QUESTION"]:
        if intent_result.intent == "QUESTION":
            answer = await generate_question_answer(
                request.message, 
                conversation.current_cart, 
                existing_constraints, 
                conversation_history
            )
            
            # Save state
            new_messages = list(conversation.messages)
            new_messages.append({
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": request.message,
                "createdAt": datetime.utcnow().isoformat() + "Z"
            })
            new_messages.append({
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": answer,
                "createdAt": datetime.utcnow().isoformat() + "Z"
            })
            conversation.messages = new_messages
            await db.commit()
            
            # Reconstruct RecommendationResult from current_cart
            computed_total = sum(item.get("subtotal", 0) for item in conversation.current_cart)
            budget_remaining = None
            if existing_constraints.get("max_budget"):
                budget_remaining = round(existing_constraints["max_budget"] - computed_total, 2)
                
            rec = RecommendationResult(
                status="Optimal",
                reason="Restored from draft",
                items=conversation.current_cart,
                computed_total=computed_total,
                budget_remaining=budget_remaining,
                total_servings=0,
                veg_servings=0,
                vegan_servings=0,
                nonveg_servings=0,
                decision_rationale=None
            )
            
            return ChatResponse(
                conversation_id=UUID(conversation.id),
                recommendation=rec,
                explanation=answer,
                extracted_constraints=ExtractedConstraints(**existing_constraints) if existing_constraints else ExtractedConstraints(),
            )
        else:
            # Short-circuit pipeline and return friendly/firm response
            if intent_result.intent == "GREETING":
                rejection_message = "Hello! Tell me about your party size, budget, or dietary preferences, and I'll build the perfect menu for you."
            else:
                rejection_message = "I can only help you with ordering food, modifying your current cart, or answering questions about the menu."
                
            # Save state
            new_messages = list(conversation.messages)
            new_messages.append({
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": request.message,
                "createdAt": datetime.utcnow().isoformat() + "Z"
            })
            new_messages.append({
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": rejection_message,
                "createdAt": datetime.utcnow().isoformat() + "Z"
            })
            conversation.messages = new_messages
            await db.commit()

            return ChatResponse(
                conversation_id=UUID(conversation.id),
                recommendation=RecommendationResult(
                    status="Infeasible",
                    reason=intent_result.reason,
                    items=[],
                    computed_total=0.0,
                    budget_remaining=0.0,
                    total_servings=0,
                    veg_servings=0,
                    vegan_servings=0,
                    nonveg_servings=0,
                    decision_rationale=None
                ),
                explanation=rejection_message,
                extracted_constraints=ExtractedConstraints(),
            )

    # --- Step 1.5: Deterministic State Merging ---
    constraints = merge_constraints(existing_constraints, delta_constraints)

    # --- Step 2: SQL Deterministic Filter ---
    filtered = await filter_menu_items(db, str(request.restaurant_id), constraints)
    veg_items = filtered["veg"]
    vegan_items = filtered["vegan"]
    nonveg_items = filtered["nonveg"]

    # --- Step 3: ILP Optimization ---
    solver_output = optimize_menu(veg_items, vegan_items, nonveg_items, constraints)

    # --- Step 4: Build structured recommendation result ---
    recommended_items = []
    veg_servings = 0
    vegan_servings = 0
    nonveg_servings = 0

    for entry in solver_output.get("items", []):
        item = entry["item"]
        item_servings = entry["quantity"] * item.serving_size
        if item.dietary_preference == 'Vegetarian':
            veg_servings += item_servings
        elif item.dietary_preference == 'Vegan':
            vegan_servings += item_servings
        else:
            nonveg_servings += item_servings

        recommended_items.append(RecommendedItem(
            id=str(item.id),
            name=item.name,
            category=item.category,
            quantity=entry["quantity"],
            unit_price=float(item.price),
            subtotal=entry["subtotal"],
            dietary_preference=item.dietary_preference,
            spice_level=item.spice_level,
            serving_size=item.serving_size,
            total_servings=item_servings,
            image_url=item.image_url,
        ))

    budget_remaining = None
    if constraints.max_budget:
        budget_remaining = round(constraints.max_budget - solver_output["total_cost"], 2)

    recommendation = RecommendationResult(
        status=solver_output["status"],
        reason=solver_output.get("reason", ""),
        items=recommended_items,
        computed_total=solver_output["total_cost"],
        budget_remaining=budget_remaining,
        total_servings=solver_output["total_servings"],
        veg_servings=veg_servings,
        vegan_servings=vegan_servings,
        nonveg_servings=nonveg_servings,
        decision_rationale=solver_output.get("decision_rationale", None)
    )

    # --- Step 5: Grounded LLM Explanation ---
    explanation = await generate_explanation(solver_output, constraints)

    # --- Step 6: Save State ---
    # Append to conversation history
    new_messages = list(conversation.messages)
    new_messages.append({
        "id": str(uuid.uuid4()),
        "role": "user",
        "content": request.message,
        "createdAt": datetime.utcnow().isoformat() + "Z"
    })
    new_messages.append({
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "content": explanation,
        "createdAt": datetime.utcnow().isoformat() + "Z"
    })
    
    conversation.messages = new_messages
    conversation.current_constraints = constraints.model_dump()
    conversation.current_cart = [item.model_dump() for item in recommended_items]
    
    await db.commit()

    return ChatResponse(
        conversation_id=UUID(conversation.id),
        recommendation=recommendation,
        explanation=explanation,
        extracted_constraints=constraints,
    )

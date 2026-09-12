"""Recommendation Pipeline Orchestrator — connects LLM, SQL Filter, ILP Solver, and Telemetry."""

import uuid
import asyncio
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
from app.services.restaurant_resolver import resolve_restaurant
from app.models.restaurant import Restaurant
from app.models.conversation import Conversation


async def process_chat_request(request: ChatRequest, db: AsyncSession, user_id: str) -> tuple[ChatResponse, dict]:
    """
    Full governed recommendation pipeline:
      0. Restaurant resolution (direct mention or cross-restaurant optimization if not provided)
      0.5 Intent Classification (Guardrail)
      1. Extract constraints from user message (LLM Delta)
      1.5 Merge delta into existing conversation state (Python Deterministic)
      2. Filter menu items from database (SQL Telemetry)
      3. Optimize meal combination (ILP Solver with Diversity Soft Penalties)
      4. Generate grounded explanation (LLM Telemetry)
    Returns:
      (ChatResponse, pipeline_telemetry_dict)
    """
    pipeline_telemetry = {
        "intent": {},
        "llm_calls": [],
        "sql_queries": [],
        "cache_hits": [],
        "solver_decision": {}
    }

    # --- Step 0: Conversation State Management ---
    conversation = None
    conversation_history = []
    existing_constraints = {}
    active_restaurant_id = str(request.restaurant_id) if request.restaurant_id else None
    active_restaurant_name = None
    cross_restaurant_meta = None

    if request.conversation_id:
        conversation = await db.get(Conversation, str(request.conversation_id))
        if conversation:
            conversation_history = conversation.messages or []
            existing_constraints = conversation.current_constraints or {}
            if not active_restaurant_id and conversation.restaurant_id:
                active_restaurant_id = str(conversation.restaurant_id)

    # --- Step 0.5 & 1: Parallel Intent Classification & Constraint Extraction ---
    (intent_result, intent_meta), (delta_constraints, extractor_meta) = await asyncio.gather(
        classify_intent(request.message),
        extract_constraints(
            request.message, 
            conversation_history=conversation_history, 
            existing_constraints=existing_constraints,
            current_cart=conversation.current_cart if conversation else None
        )
    )

    pipeline_telemetry["intent"] = intent_result.model_dump()
    pipeline_telemetry["llm_calls"].append(intent_meta)
    pipeline_telemetry["llm_calls"].append(extractor_meta)

    # --- Step 0.8: Resolve Restaurant (checks for explicit switches, cross-restaurant queries, or initial resolution) ---
    resolution = await resolve_restaurant(db, request.message, delta_constraints, current_restaurant_id=active_restaurant_id)
    switched_restaurant = False

    if resolution["status"] == "RESOLVED":
        resolved_r = resolution["restaurant"]
        resolved_id = str(resolved_r.id)
        if active_restaurant_id and active_restaurant_id != resolved_id:
            # User explicitly switched to a different restaurant (e.g. from Spice Garden while at Grand Kitchen)
            switched_restaurant = True
            active_restaurant_id = resolved_id
            active_restaurant_name = resolved_r.name
            # Reset old cart and dish-specific constraints from the previous restaurant
            if conversation:
                conversation.current_cart = []
                conversation.restaurant_id = active_restaurant_id
            general_keys = ["party_size", "vegetarians", "vegans", "non_vegetarians", "max_budget", "spice_level_preferred", "allergens"]
            existing_constraints = {k: v for k, v in existing_constraints.items() if k in general_keys and v is not None}
            if delta_constraints and hasattr(delta_constraints, "specific_dish_requests"):
                delta_constraints.specific_dish_requests = []
        elif not active_restaurant_id:
            active_restaurant_id = resolved_id
            active_restaurant_name = resolved_r.name
            if conversation:
                conversation.restaurant_id = active_restaurant_id
        else:
            active_restaurant_name = resolved_r.name

    elif resolution["status"] == "CROSS_RESTAURANT":
        resolved_r = resolution["restaurant"]
        resolved_id = str(resolved_r.id)
        if active_restaurant_id and active_restaurant_id != resolved_id:
            switched_restaurant = True
            active_restaurant_id = resolved_id
            active_restaurant_name = resolved_r.name
            if conversation:
                conversation.current_cart = []
                conversation.restaurant_id = active_restaurant_id
            general_keys = ["party_size", "vegetarians", "vegans", "non_vegetarians", "max_budget", "spice_level_preferred", "allergens"]
            existing_constraints = {k: v for k, v in existing_constraints.items() if k in general_keys and v is not None}
            if delta_constraints and hasattr(delta_constraints, "specific_dish_requests"):
                delta_constraints.specific_dish_requests = []
        elif not active_restaurant_id:
            active_restaurant_id = resolved_id
            active_restaurant_name = resolved_r.name
            if conversation:
                conversation.restaurant_id = active_restaurant_id
        else:
            active_restaurant_name = resolved_r.name

        cross_restaurant_meta = {
            "status": resolution["status"],
            "is_cross_restaurant": True,
            "comparison_summary": resolution.get("comparison_summary"),
            "candidates": resolution.get("candidate_comparisons", [])
        }

    else:
        # Ambiguous resolution or no match
        if not active_restaurant_id:
            clarification_text = resolution.get("clarification_message", "Please select or name a restaurant to proceed.")
            if not conversation:
                conversation = Conversation(
                    restaurant_id=None,
                    user_id=user_id,
                    messages=[],
                    current_constraints={},
                    current_cart=[]
                )
                db.add(conversation)
                await db.commit()
                await db.refresh(conversation)

            new_msgs = list(conversation.messages or [])
            new_msgs.append({"id": str(uuid.uuid4()), "role": "user", "content": request.message, "createdAt": datetime.now(timezone.utc).isoformat()})
            new_msgs.append({"id": str(uuid.uuid4()), "role": "assistant", "content": clarification_text, "createdAt": datetime.now(timezone.utc).isoformat()})
            conversation.messages = new_msgs
            conversation.updated_at = datetime.now(timezone.utc)
            await db.commit()

            response = ChatResponse(
                conversation_id=UUID(conversation.id),
                restaurant_id=None,
                restaurant_name=None,
                recommendation=RecommendationResult(
                    status="Infeasible",
                    reason="Restaurant not resolved",
                    items=[]
                ),
                explanation=clarification_text,
                extracted_constraints=delta_constraints,
                cross_restaurant_meta={"status": "AMBIGUOUS"}
            )
            return response, pipeline_telemetry
        else:
            # Continuing within already established active_restaurant_id
            if not active_restaurant_name:
                r_obj = await db.get(Restaurant, active_restaurant_id)
                if r_obj:
                    active_restaurant_name = r_obj.name

    # Create or update conversation record with active restaurant
    if not conversation:
        conversation = Conversation(
            restaurant_id=active_restaurant_id,
            user_id=user_id,
            messages=[],
            current_constraints={},
            current_cart=[]
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
    elif active_restaurant_id and conversation.restaurant_id != active_restaurant_id:
        conversation.restaurant_id = active_restaurant_id
        conversation.updated_at = datetime.now(timezone.utc)
        await db.commit()

    # --- Intent short-circuiting ---
    if intent_result.intent in ["OFF_TOPIC", "ADVERSARIAL", "GREETING", "QUESTION"]:
        if intent_result.intent == "QUESTION":
            answer, qa_meta = await generate_question_answer(
                request.message, 
                conversation.current_cart or [], 
                existing_constraints, 
                conversation_history
            )
            pipeline_telemetry["llm_calls"].append(qa_meta)
            
            # Save state
            new_messages = list(conversation.messages or [])
            new_messages.append({
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": request.message,
                "createdAt": datetime.now(timezone.utc).isoformat()
            })
            new_messages.append({
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": answer,
                "createdAt": datetime.now(timezone.utc).isoformat()
            })
            conversation.messages = new_messages
            conversation.updated_at = datetime.now(timezone.utc)
            await db.commit()
            
            computed_total = sum(item.get("subtotal", 0) for item in (conversation.current_cart or []))
            budget_remaining = None
            if existing_constraints.get("max_budget"):
                budget_remaining = round(existing_constraints["max_budget"] - computed_total, 2)
                
            rec = RecommendationResult(
                status="Optimal",
                reason="Restored from draft",
                items=conversation.current_cart or [],
                computed_total=computed_total,
                budget_remaining=budget_remaining,
                total_servings=0,
                veg_servings=0,
                vegan_servings=0,
                nonveg_servings=0,
                decision_rationale=None
            )
            
            chat_res = ChatResponse(
                conversation_id=UUID(conversation.id),
                restaurant_id=UUID(active_restaurant_id) if active_restaurant_id else None,
                restaurant_name=active_restaurant_name,
                recommendation=rec,
                explanation=answer,
                extracted_constraints=ExtractedConstraints(**existing_constraints) if existing_constraints else ExtractedConstraints(),
                cross_restaurant_meta=cross_restaurant_meta
            )
            return chat_res, pipeline_telemetry
        else:
            if intent_result.intent == "GREETING":
                rejection_message = f"Hello! Welcome to SmartDiner Concierge. Tell me about your party size, budget, or preferred dishes, and I'll find or design the perfect meal for you."
            else:
                rejection_message = "I can help you with finding dishes across restaurants, ordering food, modifying your cart, or answering menu questions."
                
            new_messages = list(conversation.messages or [])
            new_messages.append({
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": request.message,
                "createdAt": datetime.now(timezone.utc).isoformat()
            })
            new_messages.append({
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": rejection_message,
                "createdAt": datetime.now(timezone.utc).isoformat()
            })
            conversation.messages = new_messages
            conversation.updated_at = datetime.now(timezone.utc)
            await db.commit()

            chat_res = ChatResponse(
                conversation_id=UUID(conversation.id),
                restaurant_id=UUID(active_restaurant_id) if active_restaurant_id else None,
                restaurant_name=active_restaurant_name,
                recommendation=RecommendationResult(
                    status="Infeasible",
                    reason=intent_result.reason,
                    items=[]
                ),
                explanation=rejection_message,
                extracted_constraints=ExtractedConstraints(),
                cross_restaurant_meta=cross_restaurant_meta
            )
            return chat_res, pipeline_telemetry

    # --- Step 1.5: Deterministic State Merging ---
    constraints = merge_constraints(existing_constraints, delta_constraints)

    # --- Step 2: SQL Deterministic Filter ---
    filtered, query_meta = await filter_menu_items(db, active_restaurant_id, constraints)
    pipeline_telemetry["sql_queries"].append(query_meta)
    if "cache_event" in query_meta:
        pipeline_telemetry["cache_hits"].append(query_meta["cache_event"])
    safety_notes = query_meta.get("safety_notes", [])
    veg_items = filtered["veg"]
    vegan_items = filtered["vegan"]
    nonveg_items = filtered["nonveg"]

    # --- Step 3: ILP Optimization ---
    solver_output = optimize_menu(veg_items, vegan_items, nonveg_items, constraints)
    if safety_notes:
        if "decision_rationale" not in solver_output or not solver_output["decision_rationale"]:
            solver_output["decision_rationale"] = {}
        solver_output["decision_rationale"]["safety_notes"] = safety_notes
    pipeline_telemetry["solver_decision"] = solver_output.get("decision_rationale", {})

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
    explanation, explanation_meta = await generate_explanation(solver_output, constraints, safety_notes=safety_notes)
    pipeline_telemetry["llm_calls"].append(explanation_meta)

    # Prepend comparison summary if cross-restaurant optimization occurred
    if cross_restaurant_meta and cross_restaurant_meta.get("comparison_summary"):
        explanation = f"{cross_restaurant_meta['comparison_summary']}\n\n{explanation}"

    # --- Step 6: Save State ---
    new_messages = list(conversation.messages or [])
    new_messages.append({
        "id": str(uuid.uuid4()),
        "role": "user",
        "content": request.message,
        "createdAt": datetime.now(timezone.utc).isoformat()
    })
    new_messages.append({
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "content": explanation,
        "createdAt": datetime.now(timezone.utc).isoformat()
    })
    
    conversation.messages = new_messages
    conversation.current_constraints = constraints.model_dump()
    conversation.current_cart = [item.model_dump() for item in recommended_items]
    if active_restaurant_id:
        conversation.restaurant_id = active_restaurant_id
    conversation.updated_at = datetime.now(timezone.utc)
        
    await db.commit()

    chat_response = ChatResponse(
        conversation_id=UUID(conversation.id),
        restaurant_id=UUID(active_restaurant_id) if active_restaurant_id else None,
        restaurant_name=active_restaurant_name,
        recommendation=recommendation,
        explanation=explanation,
        extracted_constraints=constraints,
        cross_restaurant_meta=cross_restaurant_meta
    )
    return chat_response, pipeline_telemetry

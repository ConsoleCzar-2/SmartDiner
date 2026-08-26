"""Recommendation Pipeline Orchestrator — connects LLM, SQL Filter, and ILP Solver."""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.constraints import ExtractedConstraints
from app.schemas.recommendation import (
    ChatRequest, ChatResponse, RecommendationResult, RecommendedItem
)
from app.services.constraint_extractor import extract_constraints
from app.services.menu_filter import filter_menu_items
from app.services.optimizer import optimize_menu
from app.services.explanation_generator import generate_explanation
from app.models.restaurant import Restaurant


async def process_chat_request(request: ChatRequest, db: AsyncSession) -> ChatResponse:
    """
    Full recommendation pipeline:
      1. Extract constraints from user message (LLM)
      2. Filter menu items from database (SQL)
      3. Optimize meal combination (ILP Solver)
      4. Generate grounded explanation (LLM)
    """
    # --- Step 1: LLM Constraint Extraction ---
    constraints = await extract_constraints(request.message)

    # --- Step 2: SQL Deterministic Filter ---
    filtered = await filter_menu_items(db, request.restaurant_id, constraints)
    veg_items = filtered["veg"]
    nonveg_items = filtered["nonveg"]

    # --- Step 3: ILP Optimization ---
    solver_output = optimize_menu(veg_items, nonveg_items, constraints)

    # --- Step 4: Build structured recommendation result ---
    recommended_items = []
    veg_servings = 0
    nonveg_servings = 0

    for entry in solver_output.get("items", []):
        item = entry["item"]
        item_servings = entry["quantity"] * item.serving_size
        if item.is_veg:
            veg_servings += item_servings
        else:
            nonveg_servings += item_servings

        recommended_items.append(RecommendedItem(
            id=str(item.id),
            name=item.name,
            category=item.category,
            quantity=entry["quantity"],
            unit_price=float(item.price),
            subtotal=entry["subtotal"],
            is_veg=item.is_veg,
            spice_level=item.spice_level,
            serving_size=item.serving_size,
            total_servings=item_servings,
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
        nonveg_servings=nonveg_servings,
    )

    # --- Step 5: Grounded LLM Explanation ---
    explanation = await generate_explanation(solver_output, constraints)

    return ChatResponse(
        conversation_id=None,  # Will be populated in Step 9 (multi-turn)
        recommendation=recommendation,
        explanation=explanation,
        extracted_constraints=constraints,
    )

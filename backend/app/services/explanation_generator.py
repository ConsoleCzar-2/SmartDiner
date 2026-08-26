"""Grounded explanation generator using Gemini 2.5 Flash (Pipeline Step 4)."""

import json
from google import genai
from app.prompts.explanation import EXPLANATION_SYSTEM_PROMPT
from app.schemas.constraints import ExtractedConstraints
from app.config import settings


async def generate_explanation(solver_output: dict, constraints: ExtractedConstraints) -> str:
    """
    Takes the verified solver output and user constraints, asks Gemini to produce
    a brief, friendly, strictly-grounded explanation.
    """
    # Build the user-facing context block that gets injected into the prompt
    items_summary = []
    for entry in solver_output.get("items", []):
        item = entry["item"]
        items_summary.append({
            "name": item.name,
            "quantity": entry["quantity"],
            "unit_price": float(item.price),
            "subtotal": entry["subtotal"],
            "is_veg": item.is_veg,
            "category": item.category,
        })

    context_block = (
        f"VERIFIED_RESULTS:\n"
        f"Status: {solver_output['status']}\n"
        f"Items: {json.dumps(items_summary, indent=2)}\n"
        f"Total Cost: ₹{solver_output['total_cost']}\n"
        f"Total Servings: {solver_output['total_servings']}\n\n"
        f"USER_CONSTRAINTS:\n"
        f"People: {constraints.people_count}\n"
        f"Vegetarians: {constraints.vegetarian_count}\n"
        f"Budget: {'₹' + str(constraints.max_budget) if constraints.max_budget else 'No limit'}\n"
        f"Excluded Allergens: {', '.join(constraints.excluded_allergens) if constraints.excluded_allergens else 'None'}\n"
    )

    # Handle infeasible case
    if solver_output["status"] != "Optimal":
        context_block = (
            f"STATUS: Infeasible\n"
            f"REASON: {solver_output.get('reason', 'Unknown')}\n\n"
            f"USER_CONSTRAINTS:\n"
            f"People: {constraints.people_count}\n"
            f"Budget: {'₹' + str(constraints.max_budget) if constraints.max_budget else 'No limit'}\n"
        )

    client = genai.Client(api_key=settings.gemini_api_key)

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=context_block,
        config={
            "system_instruction": EXPLANATION_SYSTEM_PROMPT,
            "temperature": 0.3,
        }
    )

    return response.text

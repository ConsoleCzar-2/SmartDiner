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
            "dietary_preference": item.dietary_preference,
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
        f"IS_MODIFICATION: {'True' if constraints.is_modification else 'False'}\n"
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
        model="gemini-3.5-flash-lite",
        contents=context_block,
        config={
            "system_instruction": EXPLANATION_SYSTEM_PROMPT,
            "temperature": 0.3,
        }
    )

    return response.text

async def generate_question_answer(user_message: str, current_cart: list, constraints: dict, conversation_history: list = None) -> str:
    """
    Answers user questions about the current order without modifying it.
    """
    context_block = (
        f"CURRENT_CART:\n{json.dumps(current_cart, indent=2)}\n\n"
        f"CURRENT_CONSTRAINTS:\n{json.dumps(constraints, indent=2)}\n\n"
    )
    if conversation_history:
        context_block += "HISTORY:\n"
        for msg in conversation_history[-4:]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            context_block += f"{role.capitalize()}: {content}\n"
    
    prompt = f"{context_block}\nUSER_QUESTION: {user_message}"
    
    client = genai.Client(api_key=settings.gemini_api_key)
    response = await client.aio.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config={
            "system_instruction": "You are a helpful assistant for a food ordering app. The user is asking a question about their current order or menu. Answer briefly (2-4 sentences) based on the provided CURRENT_CART and CURRENT_CONSTRAINTS. Do not offer to modify the order unless they ask.",
            "temperature": 0.3,
        }
    )
    return response.text

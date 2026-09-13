"""Grounded explanation generator using Gemini 3.5 Flash Lite (Pipeline Step 4)."""

import json
import time
from google import genai
from app.prompts.explanation import EXPLANATION_SYSTEM_PROMPT, QUESTION_ANSWER_SYSTEM_PROMPT
from app.schemas.constraints import ExtractedConstraints
from app.config import settings


def build_explanation_context(
    solver_output: dict, 
    constraints: ExtractedConstraints, 
    safety_notes: list[str] = None
) -> str:
    """Builds the canonical user-facing context block for explanation generation."""
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

    safety_notes_block = ""
    if safety_notes:
        safety_notes_block = "SAFETY_EXCLUSION_NOTES:\n" + "\n".join(f"- {note}" for note in safety_notes) + "\n\n"

    context_block = (
        f"VERIFIED_RESULTS:\n"
        f"Status: {solver_output['status']}\n"
        f"Items: {json.dumps(items_summary, indent=2)}\n"
        f"Total Cost: ₹{solver_output['total_cost']}\n"
        f"Total Servings: {solver_output['total_servings']}\n\n"
        f"{safety_notes_block}"
        f"USER_CONSTRAINTS:\n"
        f"People: {constraints.people_count}\n"
        f"Vegetarians: {constraints.vegetarian_count}\n"
        f"Vegans: {constraints.vegan_count}\n"
        f"Budget: {'₹' + str(constraints.max_budget) if constraints.max_budget else 'No limit'}\n"
        f"Excluded Allergens: {', '.join(constraints.excluded_allergens) if constraints.excluded_allergens else 'None'}\n"
        f"IS_MODIFICATION: {'True' if constraints.is_modification else 'False'}\n"
    )

    # Handle infeasible case
    if solver_output["status"] != "Optimal":
        rationale = solver_output.get("decision_rationale", {})
        items_considered = rationale.get("items_considered", 0)
        context_block = (
            f"STATUS: Infeasible\n"
            f"DIAGNOSTIC_REASON: {solver_output.get('reason', 'Unknown')}\n\n"
            f"USER_CONSTRAINTS:\n"
            f"People: {constraints.people_count}\n"
            f"Budget: {'₹' + str(constraints.max_budget) if constraints.max_budget else 'No limit'}\n"
            f"Excluded Allergens: {', '.join(constraints.excluded_allergens) if constraints.excluded_allergens else 'None'}\n"
            f"Max Spice Level: {constraints.max_spice_level or 'Any'}\n"
            f"Preferred Cuisines: {', '.join(constraints.preferred_cuisines) if constraints.preferred_cuisines else 'Any'}\n"
            f"Candidate Items Matching Filters: {items_considered}\n"
        )

    return context_block


def build_question_answer_prompt(
    user_message: str, 
    current_cart: list, 
    constraints: dict, 
    conversation_history: list = None
) -> str:
    """Builds the canonical prompt for question answering."""
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

    return f"{context_block}\nUSER_QUESTION: {user_message}"


async def stream_explanation(
    solver_output: dict, 
    constraints: ExtractedConstraints, 
    safety_notes: list[str] = None
):
    """
    Canonical streaming generator for grounded explanations via Gemini 3.5 Flash Lite.
    Yields dicts with type 'token' (content) and finally 'done' (full_text, telemetry).
    """
    context_block = build_explanation_context(solver_output, constraints, safety_notes)
    client = genai.Client(api_key=settings.gemini_api_key)

    t0 = time.perf_counter()
    response_stream = await client.aio.models.generate_content_stream(
        model="gemini-3.5-flash-lite",
        contents=context_block,
        config={
            "system_instruction": EXPLANATION_SYSTEM_PROMPT,
            "temperature": 0.3,
        }
    )

    full_text = []
    last_usage = None
    async for chunk in response_stream:
        if getattr(chunk, "usage_metadata", None):
            last_usage = chunk.usage_metadata
        text = chunk.text or ""
        if text:
            full_text.append(text)
            yield {"type": "token", "content": text}

    t1 = time.perf_counter()
    latency_ms = round((t1 - t0) * 1000, 2)

    prompt_tokens = getattr(last_usage, "prompt_token_count", 0) or 0
    completion_tokens = getattr(last_usage, "candidates_token_count", 0) or 0
    total_tokens = getattr(last_usage, "total_token_count", 0) or (prompt_tokens + completion_tokens)

    telemetry = {
        "step": "explanation_generator",
        "model": "gemini-3.5-flash-lite",
        "temperature": 0.3,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "latency_ms": latency_ms,
        "prompt_preview": context_block[:400]
    }

    yield {"type": "done", "full_text": "".join(full_text), "telemetry": telemetry}


async def generate_explanation(
    solver_output: dict, 
    constraints: ExtractedConstraints, 
    safety_notes: list[str] = None
) -> tuple[str, dict]:
    """
    Unary adapter draining the stream_explanation generator.
    Preserves exact backwards compatibility without duplicating prompt or Gemini logic.
    Returns (explanation_text, telemetry_dict).
    """
    full_text = ""
    telemetry = {}
    async for event in stream_explanation(solver_output, constraints, safety_notes):
        if event["type"] == "done":
            full_text = event["full_text"]
            telemetry = event["telemetry"]
    return full_text, telemetry


async def stream_question_answer(
    user_message: str, 
    current_cart: list, 
    constraints: dict, 
    conversation_history: list = None
):
    """
    Canonical streaming generator for answering questions about the cart.
    Yields dicts with type 'token' (content) and finally 'done' (full_text, telemetry).
    """
    prompt = build_question_answer_prompt(user_message, current_cart, constraints, conversation_history)
    client = genai.Client(api_key=settings.gemini_api_key)

    t0 = time.perf_counter()
    response_stream = await client.aio.models.generate_content_stream(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config={
            "system_instruction": QUESTION_ANSWER_SYSTEM_PROMPT,
            "temperature": 0.3,
        }
    )

    full_text = []
    last_usage = None
    async for chunk in response_stream:
        if getattr(chunk, "usage_metadata", None):
            last_usage = chunk.usage_metadata
        text = chunk.text or ""
        if text:
            full_text.append(text)
            yield {"type": "token", "content": text}

    t1 = time.perf_counter()
    latency_ms = round((t1 - t0) * 1000, 2)

    prompt_tokens = getattr(last_usage, "prompt_token_count", 0) or 0
    completion_tokens = getattr(last_usage, "candidates_token_count", 0) or 0
    total_tokens = getattr(last_usage, "total_token_count", 0) or (prompt_tokens + completion_tokens)

    telemetry = {
        "step": "question_answer",
        "model": "gemini-3.5-flash-lite",
        "temperature": 0.3,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "latency_ms": latency_ms,
        "prompt_preview": prompt[:400]
    }

    yield {"type": "done", "full_text": "".join(full_text), "telemetry": telemetry}


async def generate_question_answer(
    user_message: str, 
    current_cart: list, 
    constraints: dict, 
    conversation_history: list = None
) -> tuple[str, dict]:
    """
    Unary adapter draining the stream_question_answer generator.
    Returns (answer_text, telemetry_dict).
    """
    full_text = ""
    telemetry = {}
    async for event in stream_question_answer(user_message, current_cart, constraints, conversation_history):
        if event["type"] == "done":
            full_text = event["full_text"]
            telemetry = event["telemetry"]
    return full_text, telemetry

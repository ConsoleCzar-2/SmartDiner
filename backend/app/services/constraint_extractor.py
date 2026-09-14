import json
import time
from google import genai
from app.schemas.constraints import ExtractedConstraints
from app.prompts.constraint_extraction import CONSTRAINT_EXTRACTION_SYSTEM_PROMPT
from app.config import settings

from typing import Optional, Any

def _project_lean_cart(cart: Optional[list]) -> list[dict]:
    """Projects cart items into lean semantic representations for constraint extraction.
    Strips internal database UUIDs, 120-character GCS image URLs, unit prices, and serving math.
    Preserves: name, quantity, category, spice_level, and dietary_preference.
    """
    if not cart:
        return []
    projected = []
    for item in cart:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        entry = {
            "name": item.get("name"),
            "quantity": item.get("quantity", 1),
        }
        if item.get("category"):
            entry["category"] = item.get("category")
        if item.get("spice_level"):
            entry["spice_level"] = item.get("spice_level")
        if item.get("dietary_preference"):
            entry["dietary_preference"] = item.get("dietary_preference")
        projected.append(entry)
    return projected


def _compact_constraints(constraints: Optional[dict]) -> dict:
    """Filters out empty, null, or default values to minimize prompt tokens."""
    if not constraints:
        return {}
    return {
        k: v for k, v in constraints.items()
        if v is not None and v != [] and v != {} and v != "Any"
    }


def _format_compact_history(conversation_history: Optional[list], max_turns: int = 2) -> str:
    """Formats last N conversation turns, compacting assistant responses to prevent token bloat."""
    if not conversation_history:
        return ""
    recent_msgs = conversation_history[-(max_turns * 2):]
    formatted = []
    for msg in recent_msgs:
        role = msg.get("role", "user")
        content = msg.get("content", "").strip()
        if role == "assistant":
            summary = content.split(".")[0] if "." in content else content[:120]
            summary = summary.strip()
            if summary:
                formatted.append(f"Assistant: {summary}.")
        else:
            formatted.append(f"User: {content}")
    if not formatted:
        return ""
    return "Previous Conversation:\n" + "\n".join(formatted) + "\n"


async def extract_constraints(user_message: str, conversation_history: list = None, 
                              existing_constraints: dict = None, current_cart: list = None) -> tuple[ExtractedConstraints, dict]:
    """
    Extracts structured constraints from a natural language user message using Gemini.
    Returns (ExtractedConstraints, telemetry_dict).
    """
    client = genai.Client(api_key=settings.gemini_api_key)

    # Format lean conversation history, constraints, and cart context
    context = ""
    compact_history = _format_compact_history(conversation_history)
    if compact_history:
        context += compact_history
            
    compacted_constraints = _compact_constraints(existing_constraints)
    if compacted_constraints:
        context += f"\nExisting Constraints:\n{json.dumps(compacted_constraints)}\n"
        
    lean_cart = _project_lean_cart(current_cart)
    if lean_cart:
        context += f"\nCurrent Draft Cart:\n{json.dumps(lean_cart)}\n"
        
    if context:
        context += "\nCurrent Request:\n"

    final_prompt = f"{context}User: {user_message}"

    schema = ExtractedConstraints.model_json_schema()
    if "properties" in schema:
        schema["required"] = list(schema["properties"].keys())
        for prop_name, prop in schema["properties"].items():
            prop.pop("default", None)
            prop.pop("title", None)
            if prop_name in ("category_min_counts", "dish_quantities"):
                prop.clear()
                prop["type"] = "array"
                prop["items"] = {"type": "string"}
                prop["description"] = f"List of {prop_name} formatted as 'Name:count', e.g. ['Bread:2', 'Beverage:2']"
            elif "anyOf" in prop:
                types = [t.get("type") for t in prop["anyOf"] if t.get("type") and t.get("type") != "null"]
                if types:
                    prop["type"] = types[0]
                    prop["nullable"] = True
                del prop["anyOf"]

    t0 = time.perf_counter()
    response = await client.aio.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=final_prompt,
        config={
            "system_instruction": CONSTRAINT_EXTRACTION_SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "response_schema": schema,
            "temperature": 0.1,
        }
    )
    t1 = time.perf_counter()
    latency_ms = round((t1 - t0) * 1000, 2)

    usage = getattr(response, "usage_metadata", None)
    prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
    completion_tokens = getattr(usage, "candidates_token_count", 0) or 0
    total_tokens = getattr(usage, "total_token_count", 0) or (prompt_tokens + completion_tokens)

    telemetry = {
        "step": "constraint_extractor",
        "model": "gemini-3.5-flash-lite",
        "temperature": 0.1,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "latency_ms": latency_ms,
        "prompt_preview": final_prompt[:500]
    }

    # Validate and return the Pydantic object
    result = ExtractedConstraints.model_validate_json(response.text)
    return result, telemetry

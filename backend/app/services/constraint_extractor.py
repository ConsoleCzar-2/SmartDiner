import json
import time
from google import genai
from app.schemas.constraints import ExtractedConstraints
from app.prompts.constraint_extraction import SYSTEM_PROMPT
from app.config import settings

async def extract_constraints(user_message: str, conversation_history: list = None, 
                              existing_constraints: dict = None, current_cart: list = None) -> tuple[ExtractedConstraints, dict]:
    """
    Extracts structured constraints from a natural language user message using Gemini.
    Returns (ExtractedConstraints, telemetry_dict).
    """
    client = genai.Client(api_key=settings.gemini_api_key)

    # Format conversation history if provided (useful for modifications)
    context = ""
    if conversation_history:
        context = "Previous Conversation:\n"
        for msg in conversation_history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            context += f"{role.capitalize()}: {content}\n"
            
    if existing_constraints:
        context += f"\nExisting Constraints (JSON):\n{json.dumps(existing_constraints, indent=2)}\n"
        
    if current_cart:
        context += f"\nCurrent Draft Cart (User may have modified this):\n{json.dumps(current_cart, indent=2)}\n"
        
    if context:
        context += "\nCurrent Request:\n"

    final_prompt = f"{context}User: {user_message}"

    schema = ExtractedConstraints.model_json_schema()
    if "properties" in schema:
        schema["required"] = list(schema["properties"].keys())
        for prop in schema["properties"].values():
            prop.pop("default", None)
            prop.pop("title", None)
            if "anyOf" in prop:
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
            "system_instruction": SYSTEM_PROMPT,
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

import time
from google import genai
from pydantic import BaseModel
from app.config import settings
from app.prompts.intent_classification import INTENT_CLASSIFICATION_PROMPT

class IntentResult(BaseModel):
    intent: str
    reason: str

async def classify_intent(user_message: str) -> tuple[IntentResult, dict]:
    """
    Classifies the user's intent into ORDER, MODIFICATION, GREETING, OFF_TOPIC, or ADVERSARIAL.
    Returns (IntentResult, telemetry_dict).
    """
    client = genai.Client(api_key=settings.gemini_api_key)
    
    schema = IntentResult.model_json_schema()
    if "properties" in schema:
        schema["required"] = list(schema["properties"].keys())
        for prop in schema["properties"].values():
            prop.pop("default", None)
            prop.pop("title", None)

    t0 = time.perf_counter()
    response = await client.aio.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=f"User: {user_message}",
        config={
            "system_instruction": INTENT_CLASSIFICATION_PROMPT,
            "response_mime_type": "application/json",
            "response_schema": schema,
            "temperature": 0.0,
        }
    )
    t1 = time.perf_counter()
    latency_ms = round((t1 - t0) * 1000, 2)

    usage = getattr(response, "usage_metadata", None)
    prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
    completion_tokens = getattr(usage, "candidates_token_count", 0) or 0
    total_tokens = getattr(usage, "total_token_count", 0) or (prompt_tokens + completion_tokens)

    telemetry = {
        "step": "intent_classifier",
        "model": "gemini-3.5-flash-lite",
        "temperature": 0.0,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "latency_ms": latency_ms,
        "prompt_preview": user_message[:200]
    }

    try:
        result = IntentResult.model_validate_json(response.text)
    except Exception:
        result = IntentResult(intent="ORDER", reason="Fallback")

    return result, telemetry

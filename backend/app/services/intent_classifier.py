import json
from google import genai
from pydantic import BaseModel
from app.config import settings
from app.prompts.intent_classification import INTENT_CLASSIFICATION_PROMPT

class IntentResult(BaseModel):
    intent: str
    reason: str

async def classify_intent(user_message: str) -> IntentResult:
    """
    Classifies the user's intent into ORDER, MODIFICATION, GREETING, OFF_TOPIC, or ADVERSARIAL.
    """
    client = genai.Client(api_key=settings.gemini_api_key)
    
    schema = IntentResult.model_json_schema()
    if "properties" in schema:
        schema["required"] = list(schema["properties"].keys())
        for prop in schema["properties"].values():
            prop.pop("default", None)
            prop.pop("title", None)

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

    try:
        return IntentResult.model_validate_json(response.text)
    except Exception:
        # Fallback if something goes wrong
        return IntentResult(intent="ORDER", reason="Fallback")

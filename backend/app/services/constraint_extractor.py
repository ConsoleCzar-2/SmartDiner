import json
from google import genai
from app.schemas.constraints import ExtractedConstraints
from app.prompts.constraint_extraction import SYSTEM_PROMPT
from app.config import settings

async def extract_constraints(user_message: str, conversation_history: list = None, existing_constraints: dict = None) -> ExtractedConstraints:
    """
    Extracts structured constraints from a natural language user message using Gemini.
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
        
    if context:
        context += "\nCurrent Request:\n"

    final_prompt = f"{context}User: {user_message}"

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=final_prompt,
        config={
            "system_instruction": SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "response_schema": ExtractedConstraints.model_json_schema(),
            "temperature": 0.1,
        }
    )

    # Validate and return the Pydantic object
    return ExtractedConstraints.model_validate_json(response.text)

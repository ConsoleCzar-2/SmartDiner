"""Chat API Router — Main recommendation endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.schemas.recommendation import ChatRequest, ChatResponse
from app.services.recommendation_pipeline import process_chat_request
from app.services.auth import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from typing import Optional
from fastapi import BackgroundTasks
from app.services.audit_logger import upload_audit_log_to_gcs

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Main recommendation endpoint.
    
    Accepts a natural language message, extracts constraints via LLM,
    filters the menu via SQL, solves the optimal combination via ILP,
    and returns a structured cart with a friendly explanation.
    """
    response = await process_chat_request(request, db, current_user.id)
    
    # Enqueue the audit log to GCS asynchronously
    background_tasks.add_task(
        upload_audit_log_to_gcs,
        conversation_id=str(response.conversation_id),
        user_id=str(current_user.id),
        restaurant_id=str(request.restaurant_id),
        user_message=request.message,
        extracted_constraints=response.extracted_constraints.model_dump(),
        solver_output={
            "status": response.recommendation.status,
            "total_cost": response.recommendation.computed_total,
            "total_servings": response.recommendation.total_servings,
            "decision_rationale": response.recommendation.decision_rationale
        },
        llm_explanation=response.explanation,
        recommended_cart=[item.model_dump() for item in response.recommendation.items]
    )
    
    return response

@router.get("/chat/active")
async def get_active_conversation(
    restaurant_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns the most recent active conversation for the user at this restaurant,
    or None if no recent active conversation exists.
    """
    # Fetch the latest conversation for this user and restaurant
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .where(Conversation.restaurant_id == restaurant_id)
        .order_by(Conversation.created_at.desc())
        .limit(1)
    )
    conv = result.scalars().first()
    
    # We could implement logic to check if conv is older than a day,
    # or if the order is already placed. For now, if one exists, return it.
    if not conv or conv.status != 'ACTIVE':
        return {"conversation_id": None, "history": []}
        
    return {
        "conversation_id": conv.id,
        "history": conv.messages,
        "current_cart": conv.current_cart
    }

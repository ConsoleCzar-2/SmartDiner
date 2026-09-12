from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from uuid import UUID
from fastapi import BackgroundTasks

from app.database import get_db
from app.schemas.recommendation import ChatRequest, ChatResponse
from app.services.recommendation_pipeline import process_chat_request
from app.services.auth import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
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
    
    Accepts a natural language message, resolves restaurant or performs cross-restaurant search,
    extracts constraints via LLM, filters the menu via SQL, solves the optimal combination via ILP,
    and returns a structured cart with a friendly explanation.
    """
    response, telemetry = await process_chat_request(request, db, current_user.id)
    
    resolved_rest_id = str(response.restaurant_id or request.restaurant_id or "unassigned")
    
    # Enqueue the enriched audit log to GCS asynchronously
    background_tasks.add_task(
        upload_audit_log_to_gcs,
        conversation_id=str(response.conversation_id),
        user_id=str(current_user.id),
        restaurant_id=resolved_rest_id,
        user_message=request.message,
        extracted_constraints=response.extracted_constraints.model_dump(),
        solver_output={
            "status": response.recommendation.status,
            "total_cost": response.recommendation.computed_total,
            "total_servings": response.recommendation.total_servings,
            "decision_rationale": response.recommendation.decision_rationale
        },
        llm_explanation=response.explanation,
        recommended_cart=[item.model_dump() for item in response.recommendation.items],
        intent=telemetry.get("intent", {}),
        pipeline_telemetry=telemetry
    )
    
    return response


@router.get("/chat/active")
async def get_active_conversation(
    restaurant_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns the most recent active conversation for the user (at this restaurant if specified,
    or across all restaurants if restaurant_id is null).
    """
    query = (
        select(Conversation)
        .where(Conversation.user_id == current_user.id, Conversation.status == 'ACTIVE')
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    )
    if restaurant_id:
        query = query.where(Conversation.restaurant_id == restaurant_id)
        
    result = await db.execute(query)
    conv = result.scalars().first()
    
    if not conv:
        return {"conversation_id": None, "history": []}
        
    return {
        "conversation_id": conv.id,
        "restaurant_id": conv.restaurant_id,
        "history": conv.messages or [],
        "current_cart": conv.current_cart or [],
        "current_constraints": conv.current_constraints or {}
    }


@router.post("/chat/abandon")
async def abandon_conversation(
    conversation_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marks an active conversation as ABANDONED so clicking 'Start fresh conversation'
    or clearing the session cleanly starts a fresh state.
    """
    if conversation_id:
        conv = await db.get(Conversation, conversation_id)
        if conv and conv.user_id == current_user.id:
            conv.status = 'ABANDONED'
            conv.updated_at = datetime.now(timezone.utc)
            await db.commit()
    else:
        result = await db.execute(
            select(Conversation).where(
                Conversation.user_id == current_user.id,
                Conversation.status == 'ACTIVE'
            )
        )
        for c in result.scalars().all():
            c.status = 'ABANDONED'
            c.updated_at = datetime.now(timezone.utc)
        await db.commit()
        
    return {"status": "success"}

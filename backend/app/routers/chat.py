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

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Main recommendation endpoint.
    
    Accepts a natural language message, extracts constraints via LLM,
    filters the menu via SQL, solves the optimal combination via ILP,
    and returns a structured cart with a friendly explanation.
    """
    return await process_chat_request(request, db, current_user.id)

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
    if not conv:
        return {"conversation_id": None, "history": []}
        
    return {
        "conversation_id": conv.id,
        "history": conv.messages,
        "current_cart": conv.current_cart
    }

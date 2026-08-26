"""Chat API Router — Main recommendation endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.recommendation import ChatRequest, ChatResponse
from app.services.recommendation_pipeline import process_chat_request

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Main recommendation endpoint.
    
    Accepts a natural language message, extracts constraints via LLM,
    filters the menu via SQL, solves the optimal combination via ILP,
    and returns a structured cart with a friendly explanation.
    """
    return await process_chat_request(request, db)

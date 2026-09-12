"""Admin Insights Chat Router — Conversational Business Intelligence with RBAC."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth import get_current_admin_user
from app.models.admin_user import AdminUser
from app.services.admin_insights import generate_admin_insight

router = APIRouter(prefix="/api/admin/insights", tags=["admin_insights"])


class AdminChatRequest(BaseModel):
    message: str


class AdminChatResponse(BaseModel):
    answer: str
    target_source: str
    data_sources: list[str]
    metrics_summary: Optional[dict] = None


@router.post("/chat", response_model=AdminChatResponse)
async def admin_chat(
    request: AdminChatRequest,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Conversational Business Intelligence for Platform and Restaurant Admins.
    Classifies prompt, queries PostgreSQL and/or GCS audit logs, and synthesizes grounded insights.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    insight_data = await generate_admin_insight(db, current_user, request.message)

    return AdminChatResponse(
        answer=insight_data["answer"],
        target_source=insight_data["target_source"],
        data_sources=insight_data["data_sources"],
        metrics_summary=insight_data["metrics_summary"]
    )

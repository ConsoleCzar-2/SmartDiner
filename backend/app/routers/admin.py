"""Admin API Router — Authentication, Metrics, and Audit Logs."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.order import Order
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.admin import LoginRequest, Token, AdminMetrics, ConversationResponse
from app.services.auth import verify_password, create_access_token, get_current_admin_user

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/metrics", response_model=AdminMetrics)
async def get_metrics(current_user: AdminUser = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    # Build base queries scoped by RBAC
    order_query = select(func.count(Order.id), func.sum(Order.total_amount))
    conv_query = select(func.count(Conversation.id))
    
    if current_user.role == "RESTAURANT_ADMIN" and current_user.restaurant_id:
        order_query = order_query.where(Order.restaurant_id == current_user.restaurant_id)
        conv_query = conv_query.where(Conversation.restaurant_id == current_user.restaurant_id)
        
    order_result = await db.execute(order_query)
    total_orders, total_revenue = order_result.one()
    
    conv_result = await db.execute(conv_query)
    total_conversations = conv_result.scalar() or 0
    
    # Mocking advanced metrics for now (will calculate dynamically later if needed)
    return AdminMetrics(
        total_orders=total_orders or 0,
        total_conversations=total_conversations,
        total_revenue=float(total_revenue or 0),
        budget_adherence_rate=100.0,
        total_servings_recommended=0
    )

@router.get("/conversations", response_model=list[ConversationResponse])
async def get_conversations(current_user: AdminUser = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    query = (
        select(Conversation, User.name.label("customer_name"))
        .outerjoin(User, Conversation.user_id == User.id)
        .order_by(Conversation.created_at.desc())
        .limit(50)
    )
    
    if current_user.role == "RESTAURANT_ADMIN" and current_user.restaurant_id:
        query = query.where(Conversation.restaurant_id == current_user.restaurant_id)
        
    result = await db.execute(query)
    rows = result.all()
    
    responses = []
    for row in rows:
        c = row.Conversation
        # Mask the ID: e.g. "Abhirup (User #4f92...)"
        masked_id = c.user_id[:4] if c.user_id else "unknown"
        customer_name = f"{row.customer_name or 'Guest'} (User #{masked_id})"
        
        responses.append(ConversationResponse(
            id=str(c.id),
            user_id=str(c.user_id) if c.user_id else None,
            customer_name=customer_name,
            restaurant_id=str(c.restaurant_id) if c.restaurant_id else None,
            messages=c.messages,
            current_constraints=c.current_constraints,
            current_cart=c.current_cart,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat()
        ))
    
    return responses

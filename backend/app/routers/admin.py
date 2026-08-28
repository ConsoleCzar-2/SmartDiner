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
from app.models.restaurant import Restaurant
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
        select(Conversation, User.name.label("customer_name"), Restaurant.name.label("restaurant_name"))
        .outerjoin(User, Conversation.user_id == User.id)
        .outerjoin(Restaurant, Conversation.restaurant_id == Restaurant.id)
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
            restaurant_name=row.restaurant_name,
            messages=c.messages,
            current_constraints=c.current_constraints,
            current_cart=c.current_cart,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat()
        ))
    
    return responses

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Conversation, User.name.label("customer_name"), Restaurant.name.label("restaurant_name"))
        .outerjoin(User, Conversation.user_id == User.id)
        .outerjoin(Restaurant, Conversation.restaurant_id == Restaurant.id)
        .where(Conversation.id == conversation_id)
    )
    
    if current_user.role == "RESTAURANT_ADMIN" and current_user.restaurant_id:
        query = query.where(Conversation.restaurant_id == current_user.restaurant_id)
        
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")
        
    c = row.Conversation
    masked_id = c.user_id[:4] if c.user_id else "unknown"
    customer_name = f"{row.customer_name or 'Guest'} (User #{masked_id})"
    
    return ConversationResponse(
        id=str(c.id),
        user_id=str(c.user_id) if c.user_id else None,
        customer_name=customer_name,
        restaurant_id=str(c.restaurant_id) if c.restaurant_id else None,
        restaurant_name=row.restaurant_name,
        messages=c.messages,
        current_constraints=c.current_constraints,
        current_cart=c.current_cart,
        created_at=c.created_at.isoformat(),
        updated_at=c.updated_at.isoformat()
    )

@router.get("/audit-logs/{conversation_id}")
async def get_audit_logs(
    conversation_id: str, 
    current_user: AdminUser = Depends(get_current_admin_user), 
    db: AsyncSession = Depends(get_db)
):
    from google.cloud import storage
    from app.config import settings
    import json
    
    # 1. Verify RBAC & Ownership
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    if current_user.role == "RESTAURANT_ADMIN" and str(conv.restaurant_id) != str(current_user.restaurant_id):
        raise HTTPException(status_code=403, detail="Not authorized to view logs for this restaurant")
        
    if not settings.gcs_audit_bucket_name:
        raise HTTPException(status_code=503, detail="Audit logging is not configured (GCS_AUDIT_BUCKET_NAME missing)")
        
    # 2. Fetch from GCS
    try:
        client = storage.Client(project=settings.gcp_project_id if settings.gcp_project_id else None)
        bucket = client.bucket(settings.gcs_audit_bucket_name)
        
        # List all blobs in this conversation's folder
        prefix = f"audit_logs/{conversation_id}/"
        blobs = list(bucket.list_blobs(prefix=prefix))
        
        if not blobs:
            return {"logs": []}
            
        logs = []
        for blob in sorted(blobs, key=lambda b: b.name, reverse=True):
            content = blob.download_as_string()
            logs.append(json.loads(content))
            
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audit logs from GCS: {str(e)}")

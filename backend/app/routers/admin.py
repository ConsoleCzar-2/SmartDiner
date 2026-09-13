from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, and_

from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.order import Order, OrderItem
from app.models.menu_item import MenuItem
from app.models.conversation import Conversation
from app.models.user import User
from app.models.restaurant import Restaurant
from app.schemas.admin import (
    LoginRequest, Token, AdminMetrics, ConversationResponse,
    AdminAnalyticsResponse, DailyTrendPoint, TopDishItem,
    CategoryDistributionItem, SolverHealthMetrics, RecentOrderItem
)
from app.services.auth import verify_password, create_access_token, get_current_admin_user
from app.services.admin_insights import fetch_gcs_audit_metrics

router = APIRouter(prefix="/api/admin", tags=["admin"])


def get_time_bounds(
    time_range: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Calculates start time, previous period start/end, granularity ('hour' or 'day'), and end_time."""
    now = datetime.now(timezone.utc)
    granularity = "day"

    if time_range == "12h":
        start = now - timedelta(hours=12)
        prev_start = start - timedelta(hours=12)
        prev_end = start
        granularity = "hour"
        return start, prev_start, prev_end, granularity, now
    elif time_range == "24h":
        start = now - timedelta(hours=24)
        prev_start = start - timedelta(hours=24)
        prev_end = start
        granularity = "hour"
        return start, prev_start, prev_end, granularity, now
    elif time_range == "today":
        start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        prev_start = start - timedelta(days=1)
        prev_end = start
        granularity = "hour"
        return start, prev_start, prev_end, granularity, now
    elif time_range == "7d":
        start = now - timedelta(days=7)
        prev_start = start - timedelta(days=7)
        prev_end = start
        granularity = "day"
        return start, prev_start, prev_end, granularity, now
    elif time_range == "90d":
        start = now - timedelta(days=90)
        prev_start = start - timedelta(days=90)
        prev_end = start
        granularity = "day"
        return start, prev_start, prev_end, granularity, now
    elif time_range == "custom":
        try:
            if start_date:
                s_dt = datetime.fromisoformat(start_date.strip())
                start = s_dt if s_dt.tzinfo else s_dt.replace(tzinfo=timezone.utc)
            else:
                start = now - timedelta(days=30)
            
            if end_date:
                e_dt = datetime.fromisoformat(end_date.strip())
                end = e_dt if e_dt.tzinfo else e_dt.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            else:
                end = now

            span = end - start
            if span.total_seconds() < 0:
                span = timedelta(days=1)
                end = start + span
            prev_start = start - span
            prev_end = start
            granularity = "hour" if span <= timedelta(days=2) else "day"
            return start, prev_start, prev_end, granularity, end
        except Exception:
            start = now - timedelta(days=30)
            prev_start = start - timedelta(days=30)
            prev_end = start
            return start, prev_start, prev_end, "day", now
    elif time_range == "all":
        return None, None, None, "day", None
    else:  # default 30d
        start = now - timedelta(days=30)
        prev_start = start - timedelta(days=30)
        prev_end = start
        granularity = "day"
        return start, prev_start, prev_end, granularity, now


@router.get("/metrics", response_model=AdminMetrics)
async def get_metrics(
    time_range: str = "30d",
    current_user: AdminUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    start_time, prev_start, prev_end, _, end_time = get_time_bounds(time_range, start_date, end_date)

    order_filter = []
    conv_filter = []
    if current_user.role == "RESTAURANT_ADMIN" and current_user.restaurant_id:
        order_filter.append(Order.restaurant_id == current_user.restaurant_id)
        conv_filter.append(Conversation.restaurant_id == current_user.restaurant_id)

    curr_order_filter = list(order_filter)
    curr_conv_filter = list(conv_filter)
    if start_time:
        curr_order_filter.append(Order.created_at >= start_time)
        curr_conv_filter.append(Conversation.created_at >= start_time)
    if end_time and time_range == "custom":
        curr_order_filter.append(Order.created_at <= end_time)
        curr_conv_filter.append(Conversation.created_at <= end_time)

    order_query = select(
        func.count(Order.id),
        func.coalesce(func.sum(Order.total_amount), 0),
        func.coalesce(func.avg(Order.total_amount), 0)
    ).where(*curr_order_filter)

    conv_query = select(func.count(Conversation.id)).where(*curr_conv_filter)

    order_result = await db.execute(order_query)
    total_orders, total_revenue, avg_order_val = order_result.one()

    conv_result = await db.execute(conv_query)
    total_conversations = conv_result.scalar() or 0

    revenue_growth_pct = None
    orders_growth_pct = None
    conversations_growth_pct = None

    if prev_start and prev_end:
        prev_order_filter = list(order_filter) + [Order.created_at >= prev_start, Order.created_at < prev_end]
        prev_conv_filter = list(conv_filter) + [Conversation.created_at >= prev_start, Conversation.created_at < prev_end]

        prev_ord_res = await db.execute(
            select(func.count(Order.id), func.coalesce(func.sum(Order.total_amount), 0)).where(*prev_order_filter)
        )
        prev_orders, prev_rev = prev_ord_res.one()

        prev_conv_res = await db.execute(select(func.count(Conversation.id)).where(*prev_conv_filter))
        prev_convs = prev_conv_res.scalar() or 0

        if prev_rev and float(prev_rev) > 0:
            revenue_growth_pct = round(((float(total_revenue) - float(prev_rev)) / float(prev_rev)) * 100, 1)
        if prev_orders and prev_orders > 0:
            orders_growth_pct = round(((total_orders - prev_orders) / prev_orders) * 100, 1)
        if prev_convs and prev_convs > 0:
            conversations_growth_pct = round(((total_conversations - prev_convs) / prev_convs) * 100, 1)

    return AdminMetrics(
        time_range=time_range,
        total_orders=total_orders or 0,
        total_conversations=total_conversations,
        total_revenue=float(total_revenue or 0),
        avg_order_value=round(float(avg_order_val or 0), 2),
        budget_adherence_rate=100.0,
        total_servings_recommended=0,
        revenue_growth_pct=revenue_growth_pct,
        orders_growth_pct=orders_growth_pct,
        conversations_growth_pct=conversations_growth_pct
    )


@router.get("/analytics", response_model=AdminAnalyticsResponse)
async def get_analytics(
    time_range: str = "30d",
    current_user: AdminUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    metrics = await get_metrics(time_range, current_user, db, start_date=start_date, end_date=end_date)
    start_time, _, _, granularity, end_time = get_time_bounds(time_range, start_date, end_date)

    order_filter = []
    if current_user.role == "RESTAURANT_ADMIN" and current_user.restaurant_id:
        order_filter.append(Order.restaurant_id == current_user.restaurant_id)
    if start_time:
        order_filter.append(Order.created_at >= start_time)
    if end_time and time_range == "custom":
        order_filter.append(Order.created_at <= end_time)

    # 1. Timeline Trends (Hourly or Daily with continuous zero-filling)
    if granularity == "hour":
        trunc_col = func.date_trunc('hour', Order.created_at)
        time_format = 'YYYY-MM-DD HH24:00'
    else:
        trunc_col = func.date_trunc('day', Order.created_at)
        time_format = 'YYYY-MM-DD'

    daily_q = (
        select(
            func.to_char(trunc_col, time_format).label("bucket"),
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            func.count(Order.id).label("orders")
        )
        .where(*order_filter)
        .group_by(trunc_col)
        .order_by(trunc_col)
    )
    daily_res = await db.execute(daily_q)
    trend_map = {row.bucket: (float(row.revenue or 0), int(row.orders or 0)) for row in daily_res.all()}

    daily_trends = []
    now = datetime.now(timezone.utc)

    if granularity == "hour":
        hours_count = 12 if time_range == "12h" else (24 if time_range == "24h" else 24)
        if time_range == "today":
            start_hour = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)
            slots = [start_hour + timedelta(hours=i) for i in range(max(now.hour + 1, 1))]
        elif time_range == "custom" and start_time and end_time:
            total_hours = max(1, min(int((end_time - start_time).total_seconds() // 3600) + 1, 48))
            slots = [start_time + timedelta(hours=i) for i in range(total_hours)]
        else:
            slots = [now - timedelta(hours=i) for i in range(hours_count - 1, -1, -1)]

        for slot in slots:
            b_key = slot.strftime("%Y-%m-%d %H:00")
            label = slot.strftime("%H:%M")
            rev, ords = trend_map.get(b_key, (0.0, 0))
            daily_trends.append(DailyTrendPoint(date=label, revenue=rev, orders=ords))
    else:
        if time_range == "7d":
            days_count = 7
        elif time_range == "90d":
            days_count = 90
        elif time_range == "custom" and start_time and end_time:
            days_count = max(1, min((end_time.date() - start_time.date()).days + 1, 120))
        elif time_range == "all":
            days_count = 30
        else:
            days_count = 30

        base_end = (end_time or now).date()
        for i in range(days_count - 1, -1, -1):
            d = base_end - timedelta(days=i)
            b_key = d.strftime("%Y-%m-%d")
            label = d.strftime("%b %d") if days_count <= 31 else d.strftime("%Y-%m-%d")
            rev, ords = trend_map.get(b_key, (0.0, 0))
            daily_trends.append(DailyTrendPoint(date=label, revenue=rev, orders=ords))

    # 2. Top Dishes with Restaurant Name
    top_dish_filter = []
    if current_user.role == "RESTAURANT_ADMIN" and current_user.restaurant_id:
        top_dish_filter.append(Order.restaurant_id == current_user.restaurant_id)
    if start_time:
        top_dish_filter.append(Order.created_at >= start_time)
    if end_time and time_range == "custom":
        top_dish_filter.append(Order.created_at <= end_time)

    top_dishes_q = (
        select(
            MenuItem.name,
            MenuItem.category,
            Restaurant.name.label("restaurant_name"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("qty_sold"),
            func.coalesce(func.sum(OrderItem.subtotal), 0).label("revenue")
        )
        .join(OrderItem, OrderItem.menu_item_id == MenuItem.id)
        .join(Order, OrderItem.order_id == Order.id)
        .outerjoin(Restaurant, MenuItem.restaurant_id == Restaurant.id)
        .where(*top_dish_filter)
        .group_by(MenuItem.id, MenuItem.name, MenuItem.category, Restaurant.name)
        .order_by(desc("qty_sold"))
        .limit(10)
    )
    top_res = await db.execute(top_dishes_q)
    top_dishes = [
        TopDishItem(
            name=r.name,
            category=r.category,
            restaurant_name=r.restaurant_name or "SmartDiner Kitchen",
            quantity_sold=r.qty_sold,
            revenue=float(r.revenue or 0)
        )
        for r in top_res.all()
    ]

    # 3. Category Distribution
    cat_q = (
        select(
            MenuItem.category,
            func.coalesce(func.sum(OrderItem.subtotal), 0).label("cat_rev"),
            func.count(OrderItem.id).label("cat_count")
        )
        .join(OrderItem, OrderItem.menu_item_id == MenuItem.id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(*top_dish_filter)
        .group_by(MenuItem.category)
    )
    cat_res = await db.execute(cat_q)
    total_rev = metrics.total_revenue
    category_distribution = []
    for r in cat_res.all():
        rev = float(r.cat_rev or 0)
        pct = round((rev / total_rev * 100), 1) if total_rev > 0 else 0.0
        category_distribution.append(
            CategoryDistributionItem(category=r.category, revenue=rev, order_count=r.cat_count, percentage=pct)
        )
    category_distribution.sort(key=lambda x: x.revenue, reverse=True)

    # 4. Solver Health & Allergen Frequency from GCS telemetry
    try:
        gcs_metrics = await asyncio.wait_for(
            asyncio.to_thread(fetch_gcs_audit_metrics, current_user),
            timeout=5.0
        )
    except Exception as gcs_err:
        logger.warning(f"GCS audit telemetry fetch timed out or failed: {gcs_err}")
        gcs_metrics = {}

    solver_data = gcs_metrics.get("solver_decisions", {})
    solver_health = SolverHealthMetrics(
        feasibility_rate_pct=solver_data.get("feasibility_rate_pct", 100.0),
        total_evaluations=solver_data.get("optimal_count", 0) + solver_data.get("infeasible_count", 0),
        optimal_count=solver_data.get("optimal_count", 0),
        infeasible_count=solver_data.get("infeasible_count", 0),
        avg_solve_time_ms=gcs_metrics.get("average_llm_latency_ms", 0.0)
    )
    allergen_freq = gcs_metrics.get("allergen_exclusions", {}).get("breakdown_by_allergen", {})

    # 5. Recent Orders
    recent_ord_q = (
        select(
            Order.id,
            Order.total_amount,
            Order.status,
            Order.created_at,
            User.name.label("customer_name"),
            Restaurant.name.label("restaurant_name"),
            func.count(OrderItem.id).label("items_count")
        )
        .outerjoin(User, Order.user_id == User.id)
        .outerjoin(Restaurant, Order.restaurant_id == Restaurant.id)
        .outerjoin(OrderItem, Order.id == OrderItem.order_id)
        .where(*order_filter)
        .group_by(Order.id, Order.total_amount, Order.status, Order.created_at, User.name, Restaurant.name)
        .order_by(desc(Order.created_at))
        .limit(10)
    )
    recent_res = await db.execute(recent_ord_q)
    recent_orders = [
        RecentOrderItem(
            id=str(r.id),
            customer_name=r.customer_name or "Guest Diner",
            restaurant_name=r.restaurant_name or "SmartDiner",
            total_amount=float(r.total_amount),
            items_count=r.items_count or 0,
            status=r.status,
            created_at=r.created_at.isoformat()
        )
        for r in recent_res.all()
    ]

    return AdminAnalyticsResponse(
        time_range=time_range,
        metrics=metrics,
        daily_trends=daily_trends,
        top_dishes=top_dishes,
        category_distribution=category_distribution,
        solver_health=solver_health,
        allergen_frequency=allergen_freq,
        recent_orders=recent_orders
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
    from app.services.gcs_client import get_storage_client
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
        client = get_storage_client()
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

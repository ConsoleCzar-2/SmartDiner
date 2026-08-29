from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.conversation import Conversation
from app.models.order import Order, OrderItem
from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant
from app.models.user import User
from app.services.auth import get_current_user
from app.schemas.order import CheckoutRequest, OrderResponse, OrderHistoryResponse, OrderItemResponse

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.post("/checkout", response_model=OrderResponse)
async def checkout(
    request: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch conversation
    query = select(Conversation).where(
        Conversation.id == request.conversation_id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(query)
    conversation = result.scalars().first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.status != 'ACTIVE':
        raise HTTPException(status_code=409, detail=f"Cannot checkout. Conversation is {conversation.status}")

    cart = conversation.current_cart
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # 4. Process cart items
    total_amount = 0.0
    order_items = []
    
    # We load the real menu items to get the current price and validate existence
    for item in cart:
        item_id = item.get("id") or item.get("menu_item_id")
        quantity = item.get("quantity", 1)
        
        menu_item_query = select(MenuItem).where(MenuItem.id == item_id)
        menu_item_result = await db.execute(menu_item_query)
        menu_item = menu_item_result.scalars().first()
        
        if not menu_item:
            raise HTTPException(status_code=400, detail=f"Menu item {item_id} not found")
        
        unit_price = float(menu_item.price)
        subtotal = unit_price * quantity
        total_amount += subtotal
        
        order_items.append(OrderItem(
            menu_item_id=menu_item.id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal
        ))

    # 5. Create Order
    new_order = Order(
        user_id=current_user.id,
        restaurant_id=conversation.restaurant_id,
        total_amount=total_amount,
        status="confirmed",
        constraints_used=conversation.current_constraints
    )
    
    db.add(new_order)
    await db.flush()  # Get new_order.id
    
    # 6. Assign order_id to items and add to DB
    for oi in order_items:
        oi.order_id = new_order.id
        db.add(oi)
        
    # 7. Update conversation status
    conversation.status = "CHECKED_OUT"
    
    await db.commit()
    await db.refresh(new_order)
    
    # Eager load for response
    order_query = select(Order).options(
        selectinload(Order.items).selectinload(OrderItem.menu_item)
    ).where(Order.id == new_order.id)
    order_result = await db.execute(order_query)
    final_order = order_result.scalars().first()
    
    # Map to response schema
    items_response = [
        OrderItemResponse(
            id=str(oi.id),
            menu_item_id=oi.menu_item_id,
            name=oi.menu_item.name,
            quantity=oi.quantity,
            unit_price=float(oi.unit_price),
            subtotal=float(oi.subtotal)
        ) for oi in final_order.items
    ]
    
    return OrderResponse(
        id=str(final_order.id),
        restaurant_id=final_order.restaurant_id,
        total_amount=float(final_order.total_amount),
        status=final_order.status,
        created_at=final_order.created_at,
        items=items_response
    )


@router.get("/history", response_model=OrderHistoryResponse)
async def get_order_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Order).options(
        selectinload(Order.items).selectinload(OrderItem.menu_item),
        selectinload(Order.restaurant)
    ).where(
        Order.user_id == current_user.id
    ).order_by(Order.created_at.desc())
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    order_responses = []
    for order in orders:
        items_response = [
            OrderItemResponse(
                id=str(oi.id),
                menu_item_id=oi.menu_item_id,
                name=oi.menu_item.name,
                quantity=oi.quantity,
                unit_price=float(oi.unit_price),
                subtotal=float(oi.subtotal)
            ) for oi in order.items
        ]
        
        order_responses.append(OrderResponse(
            id=str(order.id),
            restaurant_id=order.restaurant_id,
            restaurant_name=order.restaurant.name if order.restaurant else None,
            total_amount=float(order.total_amount),
            status=order.status,
            created_at=order.created_at,
            items=items_response
        ))
        
    return OrderHistoryResponse(
        orders=order_responses,
        total_count=len(order_responses)
    )

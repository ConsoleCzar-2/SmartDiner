from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
from app.models.conversation import Conversation
from app.models.menu_item import MenuItem
from app.models.user import User
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/cart", tags=["cart"])

class AddCartItemRequest(BaseModel):
    restaurant_id: str
    menu_item_id: str
    quantity: int = 1

class CartItemUpdate(BaseModel):
    id: str
    quantity: int

class PatchCartRequest(BaseModel):
    items: List[CartItemUpdate]

@router.get("")
async def get_active_cart(
    restaurant_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Conversation).where(
        Conversation.user_id == current_user.id,
        Conversation.restaurant_id == restaurant_id,
        Conversation.status == 'ACTIVE'
    ).order_by(Conversation.created_at.desc())
    result = await db.execute(query)
    conv = result.scalars().first()
    
    if not conv:
        return {"conversation_id": None, "cart": []}
        
    return {"conversation_id": conv.id, "cart": conv.current_cart}


@router.post("/add")
async def add_to_cart(
    request: AddCartItemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify menu item
    menu_item_query = select(MenuItem).where(
        MenuItem.id == request.menu_item_id,
        MenuItem.restaurant_id == request.restaurant_id
    )
    result = await db.execute(menu_item_query)
    menu_item = result.scalars().first()
    if not menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    # Get or create active conversation
    query = select(Conversation).where(
        Conversation.user_id == current_user.id,
        Conversation.restaurant_id == request.restaurant_id,
        Conversation.status == 'ACTIVE'
    ).order_by(Conversation.created_at.desc())
    result = await db.execute(query)
    conv = result.scalars().first()
    
    if not conv:
        conv = Conversation(
            user_id=current_user.id,
            restaurant_id=request.restaurant_id,
            messages=[],
            current_constraints={},
            current_cart=[]
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

    cart = list(conv.current_cart)
    
    # Check if item already in cart
    found = False
    for item in cart:
        if item.get("id") == request.menu_item_id or item.get("menu_item_id") == request.menu_item_id:
            item["quantity"] = item.get("quantity", 1) + request.quantity
            item["subtotal"] = item["quantity"] * float(menu_item.price)
            found = True
            break
            
    if not found:
        cart.append({
            "id": request.menu_item_id,
            "menu_item_id": request.menu_item_id,
            "name": menu_item.name,
            "category": menu_item.category,
            "quantity": request.quantity,
            "unit_price": float(menu_item.price),
            "subtotal": request.quantity * float(menu_item.price),
            "is_veg": menu_item.is_veg,
            "spice_level": menu_item.spice_level,
            "serving_size": menu_item.serving_size,
            "total_servings": request.quantity * menu_item.serving_size,
            "image_url": menu_item.image_url
        })

    conv.current_cart = cart
    await db.commit()
    
    return {"conversation_id": conv.id, "cart": conv.current_cart}


@router.patch("/{conversation_id}")
async def patch_cart(
    conversation_id: str,
    request: PatchCartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(query)
    conv = result.scalars().first()
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.status != 'ACTIVE':
        raise HTTPException(status_code=409, detail="Conversation is not active")

    cart = list(conv.current_cart)
    
    # Apply updates
    for update in request.items:
        for item in cart:
            if item.get("id") == update.id or item.get("menu_item_id") == update.id:
                if update.quantity <= 0:
                    cart.remove(item)
                else:
                    item["quantity"] = update.quantity
                    item["subtotal"] = update.quantity * item.get("unit_price", 0)
                    item["total_servings"] = update.quantity * item.get("serving_size", 1)
                break
                
    conv.current_cart = cart
    await db.commit()
    
    return {"conversation_id": conv.id, "cart": conv.current_cart}

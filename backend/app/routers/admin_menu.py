from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant
from app.models.allergen import Allergen
from app.services.auth import get_current_admin_user
from app.services.image_uploader import upload_image_to_gcs
from app.routers.menu import MENU_CACHE
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/api/admin", tags=["admin_menu"])

def verify_admin_access(current_user: AdminUser, restaurant_id: Optional[str] = None):
    if current_user.role == "PLATFORM_ADMIN":
        return True
    if current_user.role == "RESTAURANT_ADMIN":
        if restaurant_id and str(current_user.restaurant_id) != restaurant_id:
            raise HTTPException(status_code=403, detail="Not authorized for this restaurant")
        return True
    raise HTTPException(status_code=403, detail="Not authorized")

@router.get("/allergens")
async def get_all_allergens(
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin_user)
):
    verify_admin_access(current_user) # PLATFORM_ADMIN or RESTAURANT_ADMIN can access
    query = select(Allergen).order_by(Allergen.name)
    result = await db.execute(query)
    allergens = result.scalars().all()
    return allergens

@router.post("/restaurants/{restaurant_id}/menu/image")
async def upload_menu_image(
    restaurant_id: str,
    file: UploadFile = File(...),
    current_user: AdminUser = Depends(get_current_admin_user)
):
    verify_admin_access(current_user, restaurant_id)
    public_url = await upload_image_to_gcs(file, "menu_items", f"temp_{restaurant_id}")
    return {"image_url": public_url}

@router.post("/restaurants/{restaurant_id}/menu")
async def create_menu_item(
    restaurant_id: str,
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    category: str = Form(...),
    dietary_preference: str = Form("Non-Vegetarian"),
    spice_level: str = Form("None"),
    serving_size: int = Form(1),
    is_available: bool = Form(True),
    direct_allergen_ids: Optional[str] = Form(None),
    image_file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin_user)
):
    verify_admin_access(current_user, restaurant_id)
    
    new_item = MenuItem(
        restaurant_id=restaurant_id,
        name=name,
        description=description,
        price=price,
        category=category,
        dietary_preference=dietary_preference,
        spice_level=spice_level,
        serving_size=serving_size,
        is_available=is_available,
        image_url=None
    )
    
    db.add(new_item)
    await db.flush() # get new_item.id
    
    if image_file:
        public_url = await upload_image_to_gcs(image_file, "menu_items", str(new_item.id))
        new_item.image_url = public_url

    if direct_allergen_ids:
        try:
            ids = [int(x.strip()) for x in direct_allergen_ids.split(",") if x.strip()]
            if ids:
                al_query = select(Allergen).where(Allergen.id.in_(ids))
                al_result = await db.execute(al_query)
                new_item.direct_allergens = al_result.scalars().all()
        except ValueError:
            pass

    await db.commit()
    await db.refresh(new_item)
    
    # Evict cache
    MENU_CACHE.pop(restaurant_id, None)
    
    return new_item

@router.patch("/restaurants/{restaurant_id}/menu/{item_id}")
async def update_menu_item(
    restaurant_id: str,
    item_id: str,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    category: Optional[str] = Form(None),
    dietary_preference: Optional[str] = Form(None),
    spice_level: Optional[str] = Form(None),
    serving_size: Optional[int] = Form(None),
    is_available: Optional[bool] = Form(None),
    direct_allergen_ids: Optional[str] = Form(None),
    image_file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin_user)
):
    verify_admin_access(current_user, restaurant_id)
    
    query = select(MenuItem).options(selectinload(MenuItem.direct_allergens)).where(MenuItem.id == item_id, MenuItem.restaurant_id == restaurant_id)
    result = await db.execute(query)
    menu_item = result.scalars().first()
    
    if not menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
        
    if name is not None: menu_item.name = name
    if description is not None: menu_item.description = description
    if price is not None: menu_item.price = price
    if category is not None: menu_item.category = category
    if dietary_preference is not None: menu_item.dietary_preference = dietary_preference
    if spice_level is not None: menu_item.spice_level = spice_level
    if serving_size is not None: menu_item.serving_size = serving_size
    if is_available is not None: menu_item.is_available = is_available
    
    if direct_allergen_ids is not None:
        try:
            ids = [int(x.strip()) for x in direct_allergen_ids.split(",") if x.strip()]
            if ids:
                al_query = select(Allergen).where(Allergen.id.in_(ids))
                al_result = await db.execute(al_query)
                menu_item.direct_allergens = al_result.scalars().all()
            else:
                menu_item.direct_allergens = []
        except ValueError:
            pass
    
    if image_file:
        public_url = await upload_image_to_gcs(image_file, "menu_items", str(menu_item.id))
        menu_item.image_url = public_url
        
    await db.commit()
    await db.refresh(menu_item)
    
    # Evict cache
    MENU_CACHE.pop(restaurant_id, None)
    
    return menu_item

@router.delete("/restaurants/{restaurant_id}/menu/{item_id}")
async def delete_menu_item(
    restaurant_id: str,
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin_user)
):
    verify_admin_access(current_user, restaurant_id)
    
    query = select(MenuItem).where(MenuItem.id == item_id, MenuItem.restaurant_id == restaurant_id)
    result = await db.execute(query)
    menu_item = result.scalars().first()
    
    if not menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
        
    await db.delete(menu_item)
    await db.commit()
    
    # Evict cache
    MENU_CACHE.pop(restaurant_id, None)
    
    return {"message": "Menu item deleted"}

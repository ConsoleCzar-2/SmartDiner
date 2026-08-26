from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem
from app.models.ingredient import Ingredient
from app.schemas.menu import RestaurantResponse, MenuItemResponse

router = APIRouter(prefix="/api", tags=["menu"])

@router.get("/restaurants", response_model=List[RestaurantResponse])
async def get_restaurants(db: AsyncSession = Depends(get_db)):
    """Fetch all active restaurants from the database."""
    query = select(Restaurant).where(Restaurant.is_active == True)
    result = await db.execute(query)
    restaurants = result.scalars().all()
    return restaurants


@router.get("/restaurants/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(restaurant_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch a single active restaurant by ID."""
    from fastapi import HTTPException
    query = select(Restaurant).where(
        Restaurant.id == restaurant_id,
        Restaurant.is_active == True
    )
    result = await db.execute(query)
    restaurant = result.scalars().first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@router.get("/restaurants/{restaurant_id}/menu", response_model=List[MenuItemResponse])
async def get_restaurant_menu(restaurant_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch all active menu items for a specific restaurant."""
    query = select(MenuItem).options(
        selectinload(MenuItem.ingredients).selectinload(Ingredient.allergens)
    ).where(
        MenuItem.restaurant_id == restaurant_id,
        MenuItem.is_available == True
    )
    result = await db.execute(query)
    menu_items = result.scalars().all()
    
    # Extract unique allergens for each item
    for item in menu_items:
        allergens = set()
        for ingredient in item.ingredients:
            for allergen in ingredient.allergens:
                allergens.add(allergen.name)
        setattr(item, "allergens", list(allergens))
        
    return menu_items

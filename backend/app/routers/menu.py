from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.restaurant import Restaurant
from app.schemas.menu import RestaurantResponse

router = APIRouter(prefix="/api", tags=["menu"])

@router.get("/restaurants", response_model=List[RestaurantResponse])
async def get_restaurants(db: AsyncSession = Depends(get_db)):
    """Fetch all active restaurants from the database."""
    query = select(Restaurant).where(Restaurant.is_active == True)
    result = await db.execute(query)
    restaurants = result.scalars().all()
    return restaurants

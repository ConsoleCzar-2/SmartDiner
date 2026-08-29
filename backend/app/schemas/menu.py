from pydantic import BaseModel, ConfigDict
from typing import Optional


class RestaurantResponse(BaseModel):
    id: str
    name: str
    cuisine_type: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MenuItemResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    category: str
    price: float
    dietary_preference: str
    spice_level: str
    image_url: Optional[str] = None
    is_available: bool = True
    allergens: list[str] = []
    direct_allergen_ids: list[int] = []

    model_config = ConfigDict(from_attributes=True)

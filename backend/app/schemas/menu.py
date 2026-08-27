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
    is_veg: bool
    spice_level: str
    image_url: Optional[str] = None
    allergens: list[str] = []

    model_config = ConfigDict(from_attributes=True)

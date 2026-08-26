from pydantic import BaseModel, ConfigDict
from typing import Optional


class RestaurantResponse(BaseModel):
    id: str
    name: str
    cuisine_type: Optional[str] = None
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

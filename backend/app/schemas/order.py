from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class CheckoutRequest(BaseModel):
    conversation_id: str

class OrderItemResponse(BaseModel):
    id: str
    menu_item_id: str
    name: str
    quantity: int
    unit_price: float
    subtotal: float

    model_config = ConfigDict(from_attributes=True)

class OrderResponse(BaseModel):
    id: str
    restaurant_id: str
    restaurant_name: Optional[str] = None
    total_amount: float
    status: str
    created_at: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)

class OrderHistoryResponse(BaseModel):
    orders: List[OrderResponse]
    total_count: int

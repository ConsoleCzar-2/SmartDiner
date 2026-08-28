from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_name: Optional[str] = None

class AdminMetrics(BaseModel):
    total_orders: int
    total_conversations: int
    total_revenue: float
    budget_adherence_rate: float
    total_servings_recommended: int

class ConversationResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    customer_name: Optional[str] = None
    restaurant_id: Optional[str] = None
    restaurant_name: Optional[str] = None
    messages: List[Dict[str, Any]]
    current_constraints: Dict[str, Any]
    current_cart: List[Dict[str, Any]]
    created_at: str
    updated_at: str

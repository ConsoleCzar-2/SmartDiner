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
    time_range: str = "30d"
    total_orders: int
    total_conversations: int
    total_revenue: float
    avg_order_value: float = 0.0
    budget_adherence_rate: float = 100.0
    total_servings_recommended: int = 0
    revenue_growth_pct: Optional[float] = None
    orders_growth_pct: Optional[float] = None
    conversations_growth_pct: Optional[float] = None

class DailyTrendPoint(BaseModel):
    date: str
    revenue: float
    orders: int

class TopDishItem(BaseModel):
    name: str
    category: str
    restaurant_name: Optional[str] = None
    quantity_sold: int
    revenue: float

class CategoryDistributionItem(BaseModel):
    category: str
    revenue: float
    order_count: int
    percentage: float

class SolverHealthMetrics(BaseModel):
    feasibility_rate_pct: float
    total_evaluations: int
    optimal_count: int
    infeasible_count: int
    avg_solve_time_ms: float

class RecentOrderItem(BaseModel):
    id: str
    customer_name: Optional[str] = None
    restaurant_name: Optional[str] = None
    total_amount: float
    items_count: int
    status: str
    created_at: str

class AdminAnalyticsResponse(BaseModel):
    time_range: str
    metrics: AdminMetrics
    daily_trends: List[DailyTrendPoint]
    top_dishes: List[TopDishItem]
    category_distribution: List[CategoryDistributionItem]
    solver_health: SolverHealthMetrics
    allergen_frequency: Dict[str, int]
    recent_orders: List[RecentOrderItem]

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

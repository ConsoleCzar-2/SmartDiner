from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from app.schemas.constraints import ExtractedConstraints


class ChatRequest(BaseModel):
    """Incoming chat message from the user."""
    message: str = Field(..., description="The user's natural language message.")
    restaurant_id: UUID = Field(..., description="UUID of the target restaurant.")
    conversation_id: Optional[UUID] = Field(default=None, description="Existing conversation ID for multi-turn chats. None for new conversations.")


class RecommendedItem(BaseModel):
    """A single dish selected by the ILP solver."""
    id: str = Field(..., description="UUID of the menu item.")
    name: str
    category: str
    quantity: int
    unit_price: float
    subtotal: float
    is_veg: bool
    spice_level: str
    serving_size: int
    total_servings: int = Field(..., description="quantity * serving_size")


class RecommendationResult(BaseModel):
    """The structured cart output from the optimization solver."""
    status: str = Field(..., description="'Optimal' if solved, 'Infeasible' if constraints are impossible.")
    reason: str = Field(default="", description="Human-readable reason for the status.")
    items: list[RecommendedItem] = Field(default_factory=list)
    computed_total: float = Field(default=0.0)
    budget_remaining: Optional[float] = Field(default=None)
    total_servings: int = Field(default=0)
    veg_servings: int = Field(default=0)
    nonveg_servings: int = Field(default=0)


class ChatResponse(BaseModel):
    """Complete API response for the /api/chat endpoint."""
    conversation_id: Optional[UUID] = Field(default=None, description="Conversation UUID for multi-turn follow-ups.")
    recommendation: RecommendationResult
    explanation: str = Field(..., description="Brief, LLM-generated friendly summary of the recommendation.")
    extracted_constraints: ExtractedConstraints = Field(..., description="The structured constraints parsed from the user's message.")

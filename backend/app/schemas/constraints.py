from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class ExtractedConstraints(BaseModel):
    people_count: int = Field(default=1, description="Total number of diners. Must be at least 1.")
    vegetarian_count: int = Field(default=0, description="Count of vegetarian diners.")
    vegan_count: int = Field(default=0, description="Count of vegan diners.")
    non_vegetarian_count: Optional[int] = Field(default=None, description="Count of non-vegetarian diners.")
    max_budget: Optional[float] = Field(default=None, description="Total absolute budget in INR.")
    max_spice_level: Literal["None", "Low", "Medium", "High", "Extreme", "Any"] = Field(default="Any", description="Maximum tolerated spice level.")
    excluded_allergens: List[str] = Field(default_factory=list, description="List of exact allergens to exclude, e.g., ['Dairy', 'Gluten', 'Peanuts', 'Tree Nuts', 'Soy', 'Shellfish', 'Eggs', 'Sesame', 'Fish'].")
    preferred_cuisines: List[str] = Field(default_factory=list, description="List of preferred cuisines, e.g., ['North Indian', 'Chinese'].")
    preferred_categories: List[str] = Field(default_factory=list, description="List of preferred categories, e.g., ['Starter', 'Dessert'].")
    specific_dish_requests: List[str] = Field(default_factory=list, description="Names of specific dishes requested.")
    is_modification: bool = Field(default=False, description="True if the user is explicitly modifying a previous order/request.")

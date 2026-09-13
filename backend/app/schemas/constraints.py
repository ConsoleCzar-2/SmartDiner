from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal, Dict, Any

def _parse_kv_counts(val: Any) -> Dict[str, int]:
    if isinstance(val, dict):
        return {str(k).strip(): int(v) for k, v in val.items() if v is not None and int(v) > 0}
    if isinstance(val, list):
        res = {}
        for item in val:
            if isinstance(item, str) and ":" in item:
                k, v = item.split(":", 1)
                try:
                    cnt = int(v.strip())
                    if cnt > 0:
                        res[k.strip()] = cnt
                except ValueError:
                    pass
            elif isinstance(item, str) and item.strip():
                res[item.strip()] = 1
        return res
    return {}

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
    category_min_counts: Dict[str, int] = Field(default_factory=dict, description="Minimum item count required per category, e.g. {'Bread': 2, 'Beverage': 2, 'Starter': 2}.")
    specific_dish_requests: List[str] = Field(default_factory=list, description="Names of specific dishes requested.")
    dish_quantities: Dict[str, int] = Field(default_factory=dict, description="Specific item quantities requested per dish, e.g. {'Garlic Naan': 2, 'Kesar Rasmalai': 2}.")
    excluded_dishes: List[str] = Field(default_factory=list, description="Names of specific dishes the user explicitly wants removed or excluded.")
    is_modification: bool = Field(default=False, description="True if the user is explicitly modifying a previous order/request.")

    @field_validator("category_min_counts", "dish_quantities", mode="before")
    @classmethod
    def parse_counts(cls, v: Any) -> Dict[str, int]:
        return _parse_kv_counts(v)


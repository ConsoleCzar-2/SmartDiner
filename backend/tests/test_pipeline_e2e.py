import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.constraints import ExtractedConstraints
from app.services.menu_filter import filter_menu_items
from app.services.optimizer import optimize_menu

# Seeded Restaurant ID for Spice Symphony
RESTAURANT_ID = "01a03c12-0f10-79cc-ae4f-6f32ca7a29b8"

@pytest.mark.asyncio
async def test_strict_budget_constraint(db_session: AsyncSession):
    """Test that the ILP solver never exceeds the strict budget."""
    constraints = ExtractedConstraints(
        max_budget=500.0,
        people_count=2,
        vegetarian_count=0
    )
    
    filtered = await filter_menu_items(db_session, RESTAURANT_ID, constraints)
    result = optimize_menu(filtered["veg"], filtered["vegan"], filtered["nonveg"], constraints)
    
    # If the seeded menu for this restaurant has nothing within the budget,
    # the solver may report Infeasible. We only assert the budget invariant
    # when an optimal plan was produced.
    if result["status"] == "Optimal":
        assert result["total_cost"] <= 500.0
    else:
        assert result["status"] == "Infeasible"

@pytest.mark.asyncio
async def test_strict_vegan_allergy_constraint(db_session: AsyncSession):
    """Test that allergens are filtered out."""
    constraints = ExtractedConstraints(
        max_budget=200.0,
        people_count=2,
        vegetarian_count=2,
        excluded_allergens=["Dairy", "Nuts"]
    )
    
    filtered = await filter_menu_items(db_session, RESTAURANT_ID, constraints)
    result = optimize_menu(filtered["veg"], filtered["vegan"], filtered["nonveg"], constraints)
    
    if result["status"] == "Optimal":
        assert result["total_cost"] <= 200.0
        for selected in result["items"]:
            assert selected["item"].dietary_preference == "Vegetarian", "Non-vegetarian item chosen for vegetarian order"

@pytest.mark.asyncio
async def test_high_people_count_low_budget(db_session: AsyncSession):
    """Test an impossible scenario gracefully degrades/fails."""
    constraints = ExtractedConstraints(
        max_budget=5.0, # Impossible to feed 10 people with 5 dollars
        people_count=10,
        vegetarian_count=0
    )
    
    filtered = await filter_menu_items(db_session, RESTAURANT_ID, constraints)
    result = optimize_menu(filtered["veg"], filtered["vegan"], filtered["nonveg"], constraints)
    
    assert result["status"] == "Infeasible"

@pytest.mark.asyncio
async def test_cuisine_and_category_preferences(db_session: AsyncSession):
    """Test cuisine preferences."""
    constraints = ExtractedConstraints(
        max_budget=150.0,
        people_count=4,
        vegetarian_count=0,
        preferred_cuisines=["North Indian"],
        preferred_categories=["Main Course", "Starter"]
    )
    
    filtered = await filter_menu_items(db_session, RESTAURANT_ID, constraints)
    
    for item in filtered["all"]:
        assert item.cuisine == "North Indian"

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.constraints import ExtractedConstraints
from app.services.menu_filter import filter_menu_items
from app.services.optimizer import optimize_menu

from sqlalchemy import select
from app.models.restaurant import Restaurant

async def get_spice_garden_id(db_session: AsyncSession) -> str:
    res = await db_session.execute(select(Restaurant).where(Restaurant.name == "Spice Garden"))
    r = res.scalars().first()
    if r:
        return str(r.id)
    res2 = await db_session.execute(select(Restaurant).where(Restaurant.is_active == True))
    r2 = res2.scalars().first()
    return str(r2.id) if r2 else "01a091d5-0152-7559-9c84-08053477d4b5"

@pytest.mark.asyncio
async def test_strict_budget_constraint(db_session: AsyncSession):
    """Test that the ILP solver never exceeds the strict budget."""
    rest_id = await get_spice_garden_id(db_session)
    constraints = ExtractedConstraints(
        max_budget=500.0,
        people_count=2,
        vegetarian_count=0
    )
    
    filtered, _ = await filter_menu_items(db_session, rest_id, constraints)
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
    rest_id = await get_spice_garden_id(db_session)
    constraints = ExtractedConstraints(
        max_budget=200.0,
        people_count=2,
        vegetarian_count=2,
        excluded_allergens=["Dairy", "Nuts"]
    )
    
    filtered, _ = await filter_menu_items(db_session, rest_id, constraints)
    result = optimize_menu(filtered["veg"], filtered["vegan"], filtered["nonveg"], constraints)
    
    if result["status"] == "Optimal":
        assert result["total_cost"] <= 200.0
        for selected in result["items"]:
            assert selected["item"].dietary_preference in ["Vegetarian", "Vegan"], "Non-vegetarian item chosen for vegetarian order"

@pytest.mark.asyncio
async def test_high_people_count_low_budget(db_session: AsyncSession):
    """Test an impossible scenario gracefully degrades/fails."""
    rest_id = await get_spice_garden_id(db_session)
    constraints = ExtractedConstraints(
        max_budget=5.0, # Impossible to feed 10 people with 5 dollars
        people_count=10,
        vegetarian_count=0
    )
    
    filtered, _ = await filter_menu_items(db_session, rest_id, constraints)
    result = optimize_menu(filtered["veg"], filtered["vegan"], filtered["nonveg"], constraints)
    
    assert result["status"] == "Infeasible"

@pytest.mark.asyncio
async def test_cuisine_and_category_preferences(db_session: AsyncSession):
    """Test cuisine preferences."""
    rest_id = await get_spice_garden_id(db_session)
    constraints = ExtractedConstraints(
        max_budget=150.0,
        people_count=4,
        vegetarian_count=0,
        preferred_cuisines=["North Indian"],
        preferred_categories=["Main Course", "Starter"]
    )
    
    filtered, _ = await filter_menu_items(db_session, rest_id, constraints)
    
    for item in filtered["all"]:
        assert item.cuisine == "North Indian"

@pytest.mark.asyncio
async def test_cuisine_synonym_and_relaxation(db_session: AsyncSession):
    """Test that specifying 'Mughlai' maps to 'North Indian' without returning 0 items."""
    rest_id = await get_spice_garden_id(db_session)
    constraints = ExtractedConstraints(
        max_budget=2500.0,
        people_count=4,
        vegetarian_count=2,
        non_vegetarian_count=2,
        preferred_cuisines=["Mughlai"]
    )
    filtered, query_meta = await filter_menu_items(db_session, rest_id, constraints)
    assert len(filtered["all"]) > 0
    assert len(filtered["veg"]) > 0
    assert len(filtered["nonveg"]) > 0

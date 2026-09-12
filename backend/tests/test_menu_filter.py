import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem
from app.models.allergen import Allergen
from app.models.ingredient import Ingredient, MenuItemIngredient, IngredientAllergen
from app.schemas.constraints import ExtractedConstraints
from app.services.menu_filter import filter_menu_items

# We use an in-memory SQLite database for rapid, isolated testing
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create all tables explicitly to avoid JSONB SQLite compilation errors
    tables_to_create = [
        Restaurant.__table__,
        Allergen.__table__,
        Ingredient.__table__,
        MenuItem.__table__,
        MenuItemIngredient.__table__,
        IngredientAllergen.__table__
    ]
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=tables_to_create)
        
    async with async_session() as session:
        yield session
        
    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all, tables=tables_to_create)
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def seed_data(db_session: AsyncSession):
    """Seeds the in-memory database with test data for filtering."""
    
    # 1. Restaurant
    rest = Restaurant(id="rest-1", name="Test Kitchen", is_active=True)
    db_session.add(rest)
    
    # 2. Allergens & Ingredients
    dairy = Allergen(name="Dairy")
    peanuts = Allergen(name="Peanuts")
    
    cheese = Ingredient(name="Cheese")
    peanut_sauce = Ingredient(name="Peanut Sauce")
    chicken = Ingredient(name="Chicken")
    
    db_session.add_all([dairy, peanuts, cheese, peanut_sauce, chicken])
    await db_session.commit()
    
    # Link Ingredients -> Allergens
    db_session.add(IngredientAllergen(ingredient_id=cheese.id, allergen_id=dairy.id))
    db_session.add(IngredientAllergen(ingredient_id=peanut_sauce.id, allergen_id=peanuts.id))
    
    # 3. Menu Items
    # Item 1: Available, Veg, Medium Spice, 200 price (Contains Dairy)
    item_1 = MenuItem(
        id="item-1", restaurant_id="rest-1", name="Paneer Tikka", category="Starter",
        price=200.0, dietary_preference="Vegetarian", spice_level="Medium", cuisine="North Indian",
        serving_size=2, is_available=True
    )
    # Item 2: Available, Non-Veg, High Spice, 400 price (Contains Peanuts)
    item_2 = MenuItem(
        id="item-2", restaurant_id="rest-1", name="Kung Pao Chicken", category="Main Course",
        price=400.0, dietary_preference="Non-Vegetarian", spice_level="High", cuisine="Chinese",
        serving_size=2, is_available=True
    )
    # Item 3: Unavailable
    item_3 = MenuItem(
        id="item-3", restaurant_id="rest-1", name="Out of Stock Item", category="Starter",
        price=100.0, dietary_preference="Vegetarian", spice_level="None", cuisine="North Indian",
        serving_size=1, is_available=False
    )
    # Item 4: Available, Veg, None Spice, 50 price (No Allergens)
    item_4 = MenuItem(
        id="item-4", restaurant_id="rest-1", name="Plain Naan", category="Bread",
        price=50.0, dietary_preference="Vegetarian", spice_level="None", cuisine="North Indian",
        serving_size=1, is_available=True
    )
    
    db_session.add_all([item_1, item_2, item_3, item_4])
    await db_session.commit()
    
    # Link MenuItems -> Ingredients
    db_session.add(MenuItemIngredient(menu_item_id=item_1.id, ingredient_id=cheese.id))
    db_session.add(MenuItemIngredient(menu_item_id=item_2.id, ingredient_id=chicken.id))
    db_session.add(MenuItemIngredient(menu_item_id=item_2.id, ingredient_id=peanut_sauce.id))
    
    await db_session.commit()
    return "rest-1"


pytestmark = pytest.mark.asyncio

async def test_filter_availability(db_session, seed_data):
    rest_id = seed_data
    constraints = ExtractedConstraints()
    
    result, meta = await filter_menu_items(db_session, rest_id, constraints)
    
    assert len(result["all"]) == 3
    assert not any(item.id == "item-3" for item in result["all"])
    assert "compiled_sql" in meta
    assert isinstance(meta["duration_ms"], float)

async def test_filter_spice_logic(db_session, seed_data):
    rest_id = seed_data
    constraints = ExtractedConstraints(max_spice_level="Low")
    
    result, meta = await filter_menu_items(db_session, rest_id, constraints)
    
    assert len(result["all"]) == 1
    assert result["all"][0].id == "item-4"

async def test_filter_deep_allergens(db_session, seed_data):
    rest_id = seed_data
    constraints = ExtractedConstraints(excluded_allergens=["Dairy"])
    
    result, meta = await filter_menu_items(db_session, rest_id, constraints)
    
    assert len(result["all"]) == 2
    assert not any(item.id == "item-1" for item in result["all"])
    assert any(item.id == "item-2" for item in result["all"])
    assert any(item.id == "item-4" for item in result["all"])

async def test_filter_budget_ceiling(db_session, seed_data):
    rest_id = seed_data
    constraints = ExtractedConstraints(max_budget=300.0)
    
    result, meta = await filter_menu_items(db_session, rest_id, constraints)
    
    assert len(result["all"]) == 2
    assert not any(item.id == "item-2" for item in result["all"])

async def test_filter_cuisines(db_session, seed_data):
    rest_id = seed_data
    constraints = ExtractedConstraints(preferred_cuisines=["Chinese"])
    
    result, meta = await filter_menu_items(db_session, rest_id, constraints)
    
    assert len(result["all"]) == 1
    assert result["all"][0].id == "item-2"

async def test_veg_nonveg_split(db_session, seed_data):
    rest_id = seed_data
    constraints = ExtractedConstraints()
    
    result, meta = await filter_menu_items(db_session, rest_id, constraints)
    
    assert len(result["veg"]) == 2
    assert len(result["nonveg"]) == 1
    assert result["nonveg"][0].id == "item-2"

async def test_menu_filter_cache_hit_and_miss(db_session, seed_data):
    from app.services.menu_filter import clear_menu_filter_cache
    clear_menu_filter_cache()
    
    rest_id = seed_data
    constraints = ExtractedConstraints(max_budget=500.0, max_spice_level="Medium")
    
    # 1. First call -> Cache MISS
    res1, meta1 = await filter_menu_items(db_session, rest_id, constraints)
    assert "cache_event" in meta1
    assert meta1["cache_event"]["status"] == "MISS"
    assert meta1["cache_event"]["hit"] is False
    assert meta1["cache_event"]["action"] == "STORED"
    
    # 2. Second call with same constraints -> Cache HIT
    res2, meta2 = await filter_menu_items(db_session, rest_id, constraints)
    assert "cache_event" in meta2
    assert meta2["cache_event"]["status"] == "HIT"
    assert meta2["cache_event"]["hit"] is True
    assert meta2["cache_event"]["duration_ms"] < 5.0
    assert len(res2["all"]) == len(res1["all"])
    
    # 3. Evict cache -> Next call is MISS
    clear_menu_filter_cache(rest_id)
    res3, meta3 = await filter_menu_items(db_session, rest_id, constraints)
    assert meta3["cache_event"]["status"] == "MISS"


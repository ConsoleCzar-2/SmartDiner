import pytest
from app.services.optimizer import optimize_menu
from app.schemas.constraints import ExtractedConstraints
from app.models.menu_item import MenuItem
import uuid

# Mock items helper
def create_mock_item(name, category, price, dietary, serving_size, rating):
    item = MenuItem(
        id=uuid.uuid4(),
        restaurant_id=uuid.uuid4(),
        name=name,
        category=category,
        price=price,
        dietary_preference=dietary,
        spice_level="Low",
        cuisine="Indian",
        serving_size=serving_size,
        is_available=True,
        rating=rating
    )
    return item

@pytest.fixture
def mock_menu():
    veg_items = [
        create_mock_item("Dal Makhani", "Main Course", 300.0, "Vegetarian", 2, 4.5),
        create_mock_item("Paneer Tikka", "Starter", 400.0, "Vegetarian", 2, 4.7),
        create_mock_item("Naan", "Bread", 50.0, "Vegetarian", 1, 4.0),
    ]
    vegan_items = [
        create_mock_item("Aloo Gobi", "Main Course", 250.0, "Vegan", 2, 4.3),
        create_mock_item("Vegan Tofu Curry", "Main Course", 350.0, "Vegan", 2, 4.4),
    ]
    nonveg_items = [
        create_mock_item("Butter Chicken", "Main Course", 500.0, "Non-Vegetarian", 2, 4.8),
        create_mock_item("Chicken Biryani", "Rice", 450.0, "Non-Vegetarian", 2, 4.6),
        create_mock_item("Chicken Tikka", "Starter", 320.0, "Non-Vegetarian", 2, 4.7),
    ]
    return veg_items, vegan_items, nonveg_items

def test_optimizer_respects_budget(mock_menu):
    veg_items, vegan_items, nonveg_items = mock_menu
    
    constraints = ExtractedConstraints(
        people_count=2,
        vegetarian_count=0,
        vegan_count=0,
        non_vegetarian_count=2,
        max_budget=1000.0
    )
    
    result = optimize_menu(veg_items, vegan_items, nonveg_items, constraints)
    
    assert result["status"] == "Optimal"
    assert result["total_cost"] <= 1000.0
    assert result["total_servings"] >= 2

def test_optimizer_meets_serving_requirements(mock_menu):
    veg_items, vegan_items, nonveg_items = mock_menu
    
    constraints = ExtractedConstraints(
        people_count=5, # Need 5 servings minimum
        non_vegetarian_count=5,
        max_budget=5000.0
    )
    
    result = optimize_menu(veg_items, vegan_items, nonveg_items, constraints)
    
    assert result["status"] == "Optimal"
    assert result["total_servings"] >= 5

def test_optimizer_veg_split(mock_menu):
    veg_items, vegan_items, nonveg_items = mock_menu
    
    constraints = ExtractedConstraints(
        people_count=4,
        vegetarian_count=2, # Need at least 2 veg servings
        non_vegetarian_count=2,
        max_budget=3000.0
    )
    
    result = optimize_menu(veg_items, vegan_items, nonveg_items, constraints)
    
    assert result["status"] == "Optimal"
    
    # Verify veg servings
    veg_servings = sum(item["quantity"] * item["item"].serving_size for item in result["items"] if (item["item"].dietary_preference in ["Vegetarian", "Vegan"]))
    assert veg_servings >= 2
    assert result["total_servings"] >= 4

def test_optimizer_infeasible_budget(mock_menu):
    veg_items, vegan_items, nonveg_items = mock_menu
    
    constraints = ExtractedConstraints(
        people_count=10,
        non_vegetarian_count=10,
        max_budget=100.0 # Too low to feed 10 people
    )
    
    result = optimize_menu(veg_items, vegan_items, nonveg_items, constraints)
    
    assert result["status"] == "Infeasible"
    assert result["total_cost"] == 0.0
    assert len(result["items"]) == 0

def test_optimizer_no_veg_options_but_veg_requested():
    veg_items = []
    vegan_items = []
    nonveg_items = [create_mock_item("Butter Chicken", "Main", 500.0, "Non-Vegetarian", 2, 4.8)]
    
    constraints = ExtractedConstraints(
        people_count=2,
        vegetarian_count=2, # Veg requested
        non_vegetarian_count=0,
        max_budget=1000.0
    )
    
    result = optimize_menu(veg_items, vegan_items, nonveg_items, constraints)
    
    assert result["status"] == "Infeasible"

def test_all_veg_no_nonveg(mock_menu):
    veg_items, vegan_items, nonveg_items = mock_menu
    
    constraints = ExtractedConstraints(
        people_count=4,
        vegetarian_count=4,
        non_vegetarian_count=0,
        max_budget=3000.0
    )
    
    result = optimize_menu(veg_items, vegan_items, nonveg_items, constraints)
    assert result["status"] == "Optimal"
    
    nonveg_servings = sum(item["quantity"] * item["item"].serving_size for item in result["items"] if item["item"].dietary_preference == "Non-Vegetarian")
    assert nonveg_servings == 0

def test_specific_dish_included(mock_menu):
    veg_items, vegan_items, nonveg_items = mock_menu
    
    constraints = ExtractedConstraints(
        people_count=4,
        non_vegetarian_count=4,
        max_budget=4000.0,
        specific_dish_requests=["biryani", "aloo gobi"]
    )
    
    result = optimize_menu(veg_items, vegan_items, nonveg_items, constraints)
    assert result["status"] == "Optimal"
    
    names = [item["item"].name.lower() for item in result["items"]]
    assert any("biryani" in name for name in names)
    assert any("aloo gobi" in name for name in names)

def test_category_diversity(mock_menu):
    veg_items, vegan_items, nonveg_items = mock_menu
    
    constraints = ExtractedConstraints(
        people_count=6,
        non_vegetarian_count=6,
        max_budget=5000.0
    )
    
    result = optimize_menu(veg_items, vegan_items, nonveg_items, constraints)
    assert result["status"] == "Optimal"
    
    categories = set(item["item"].category for item in result["items"])
    # 6 people -> min 3 categories
    assert len(categories) >= 3

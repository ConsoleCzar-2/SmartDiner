import pytest
from app.services.optimizer import optimize_menu
from app.schemas.constraints import ExtractedConstraints
from app.models.menu_item import MenuItem
import uuid

# Mock items helper
def create_mock_item(name, price, is_veg, serving_size, rating):
    item = MenuItem(
        id=uuid.uuid4(),
        restaurant_id=uuid.uuid4(),
        name=name,
        price=price,
        dietary_preference="Vegetarian" if is_veg else "Non-Vegetarian",
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
        create_mock_item("Dal Makhani", 300.0, True, 2, 4.5),
        create_mock_item("Paneer Tikka", 400.0, True, 2, 4.7),
        create_mock_item("Naan", 50.0, True, 1, 4.0),
    ]
    nonveg_items = [
        create_mock_item("Butter Chicken", 500.0, False, 2, 4.8),
        create_mock_item("Chicken Biryani", 450.0, False, 2, 4.6),
    ]
    return veg_items, nonveg_items

def test_optimizer_respects_budget(mock_menu):
    veg_items, nonveg_items = mock_menu
    
    constraints = ExtractedConstraints(
        people_count=2,
        vegetarian_count=0,
        max_budget=1000.0
    )
    
    result = optimize_menu(veg_items, nonveg_items, constraints)
    
    assert result["status"] == "Optimal"
    assert result["total_cost"] <= 1000.0
    assert result["total_servings"] >= 2

def test_optimizer_meets_serving_requirements(mock_menu):
    veg_items, nonveg_items = mock_menu
    
    constraints = ExtractedConstraints(
        people_count=5, # Need 5 servings minimum
        vegetarian_count=0,
        max_budget=5000.0
    )
    
    result = optimize_menu(veg_items, nonveg_items, constraints)
    
    assert result["status"] == "Optimal"
    assert result["total_servings"] >= 5

def test_optimizer_veg_split(mock_menu):
    veg_items, nonveg_items = mock_menu
    
    constraints = ExtractedConstraints(
        people_count=4,
        vegetarian_count=2, # Need at least 2 veg servings
        max_budget=3000.0
    )
    
    result = optimize_menu(veg_items, nonveg_items, constraints)
    
    assert result["status"] == "Optimal"
    
    # Verify veg servings
    veg_servings = sum(item["quantity"] * item["item"].serving_size for item in result["items"] if (item["item"].dietary_preference == "Vegetarian"))
    assert veg_servings >= 2
    assert result["total_servings"] >= 4

def test_optimizer_infeasible_budget(mock_menu):
    veg_items, nonveg_items = mock_menu
    
    constraints = ExtractedConstraints(
        people_count=10,
        vegetarian_count=0,
        max_budget=100.0 # Too low to feed 10 people
    )
    
    result = optimize_menu(veg_items, nonveg_items, constraints)
    
    assert result["status"] == "Infeasible"
    assert result["total_cost"] == 0.0
    assert len(result["items"]) == 0

def test_optimizer_no_veg_options_but_veg_requested():
    veg_items = []
    nonveg_items = [create_mock_item("Butter Chicken", 500.0, False, 2, 4.8)]
    
    constraints = ExtractedConstraints(
        people_count=2,
        vegetarian_count=2, # Veg requested
        max_budget=1000.0
    )
    
    result = optimize_menu(veg_items, nonveg_items, constraints)
    
    assert result["status"] == "Infeasible"
    assert "No vegetarian items left" in result["reason"]

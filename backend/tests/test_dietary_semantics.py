import pytest
from app.services.optimizer import optimize_menu
from app.schemas.constraints import ExtractedConstraints
from app.models.menu_item import MenuItem
import uuid

def make_item(name, category, price, dietary, serving_size=1, rating=4.5):
    return MenuItem(
        id=uuid.uuid4(),
        restaurant_id=uuid.uuid4(),
        name=name,
        category=category,
        price=price,
        dietary_preference=dietary,
        spice_level="Low",
        cuisine="Continental",
        serving_size=serving_size,
        is_available=True,
        rating=rating
    )

@pytest.fixture
def sample_items():
    veg_items = [
        make_item("Whipped Feta Crostini", "Starter", 260.0, "Vegetarian", 1, 4.8),
        make_item("Burrata Truffle Pasta", "Main Course", 390.0, "Vegetarian", 1, 4.9),
    ]
    vegan_items = [
        make_item("Avocado Sourdough Tartine", "Starter", 240.0, "Vegan", 1, 4.6),
        make_item("Buddha Bowl", "Main Course", 360.0, "Vegan", 1, 4.7),
        make_item("Detox Green Juice", "Beverage", 160.0, "Vegan", 1, 4.5),
    ]
    nonveg_items = [
        make_item("Chicken Caesar Salad", "Starter", 320.0, "Non-Vegetarian", 1, 4.5),
        make_item("Pepperoni Pizza", "Main Course", 450.0, "Non-Vegetarian", 1, 4.8),
    ]
    return veg_items, vegan_items, nonveg_items

def test_vegetarian_request_can_recommend_vegan_items(sample_items):
    veg_items, vegan_items, nonveg_items = sample_items
    constraints = ExtractedConstraints(
        people_count=2,
        vegetarian_count=2,
        vegan_count=0,
        non_vegetarian_count=0,
        max_budget=1500.0
    )
    result = optimize_menu(veg_items, vegan_items, nonveg_items, constraints)
    assert result["status"] == "Optimal"
    
    # 0 Non-veg items allowed
    for entry in result["items"]:
        assert entry["item"].dietary_preference in ["Vegetarian", "Vegan"]
    
    # All items are vegetarian-safe (either Vegetarian or Vegan)
    assert result["total_servings"] >= 2

def test_strictly_vegan_request_never_recommends_dairy_vegetarian_items(sample_items):
    veg_items, vegan_items, nonveg_items = sample_items
    constraints = ExtractedConstraints(
        people_count=2,
        vegetarian_count=0,
        vegan_count=2,
        non_vegetarian_count=0,
        max_budget=1500.0
    )
    result = optimize_menu(veg_items, vegan_items, nonveg_items, constraints)
    assert result["status"] == "Optimal"
    
    # Every single item MUST be Vegan. Zero Vegetarian (dairy/cheese) items!
    for entry in result["items"]:
        assert entry["item"].dietary_preference == "Vegan"
        assert entry["item"].dietary_preference != "Vegetarian"
        assert entry["item"].dietary_preference != "Non-Vegetarian"

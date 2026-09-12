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

def test_optimizer_soft_meal_structure(mock_menu):
    veg_items, vegan_items, nonveg_items = mock_menu
    # Add dessert item
    dessert_item = create_mock_item("Gulab Jamun", "Dessert", 150.0, "Vegetarian", 1, 4.8)
    all_veg = veg_items + [dessert_item]

    constraints = ExtractedConstraints(
        people_count=4,
        vegetarian_count=2,
        non_vegetarian_count=2,
        max_budget=3000.0
    )

    result = optimize_menu(all_veg, vegan_items, nonveg_items, constraints)
    assert result["status"] == "Optimal"
    categories = set(item["item"].category for item in result["items"])
    # Should include Starter, Main Course, and Dessert
    assert "Main Course" in categories
    assert "Starter" in categories
    assert "Dessert" in categories

def test_optimizer_decision_rationale_telemetry(mock_menu):
    veg_items, vegan_items, nonveg_items = mock_menu
    constraints = ExtractedConstraints(
        people_count=3,
        vegetarian_count=3,
        non_vegetarian_count=0,
        max_budget=2000.0
    )
    result = optimize_menu(veg_items, vegan_items, nonveg_items, constraints)
    assert result["status"] == "Optimal"
    rationale = result["decision_rationale"]
    assert "objective_value" in rationale
    assert "solve_time_ms" in rationale
    assert "items_considered" in rationale
    assert "items_selected" in rationale
    assert "constraint_actuals" in rationale
    assert rationale["constraint_actuals"]["budget"]["used"] <= 2000.0

def test_strictly_vegan_party(mock_menu):
    veg_items, vegan_items, nonveg_items = mock_menu
    constraints = ExtractedConstraints(
        people_count=2,
        vegetarian_count=0,
        vegan_count=2,
        non_vegetarian_count=0,
        max_budget=1500.0
    )
    result = optimize_menu(veg_items, vegan_items, nonveg_items, constraints)
    assert result["status"] == "Optimal"
    # Every single item in the solution MUST be Vegan (no Vegetarian, no Non-Vegetarian)
    for entry in result["items"]:
        assert entry["item"].dietary_preference == "Vegan"
    assert result["total_servings"] >= 2

def test_mixed_vegan_and_vegetarian_party(mock_menu):
    veg_items, vegan_items, nonveg_items = mock_menu
    constraints = ExtractedConstraints(
        people_count=3,
        vegetarian_count=2,
        vegan_count=1,
        non_vegetarian_count=0,
        max_budget=2000.0
    )
    result = optimize_menu(veg_items, vegan_items, nonveg_items, constraints)
    assert result["status"] == "Optimal"
    # No non-vegetarian dishes allowed
    for entry in result["items"]:
        assert entry["item"].dietary_preference in ["Vegetarian", "Vegan"]
    # At least 1 vegan serving must be present
    vegan_servings = sum(entry["quantity"] * entry["item"].serving_size for entry in result["items"] if entry["item"].dietary_preference == "Vegan")
    assert vegan_servings >= 1


def test_dinner_for_two_prioritizes_main_course():
    """Verify that a dinner for 2 includes a Main Course even if sides and beverages are cheaper."""
    sides = [create_mock_item("Sweet Potato Wedges", "Side", 160.0, "Vegan", 1, 4.0)]
    drinks = [
        create_mock_item("Oat Milk Latte", "Beverage", 180.0, "Vegan", 1, 4.0),
        create_mock_item("Green Juice", "Beverage", 160.0, "Vegan", 1, 4.0),
    ]
    desserts = [create_mock_item("Cacao Truffles", "Dessert", 190.0, "Vegan", 1, 4.0)]
    mains = [create_mock_item("Vegan Pesto Pasta", "Main Course", 340.0, "Vegan", 1, 4.0)]

    vegan_items = sides + drinks + desserts + mains
    constraints = ExtractedConstraints(
        people_count=2,
        vegetarian_count=0,
        vegan_count=2,
        non_vegetarian_count=0,
        max_budget=1000.0,
    )
    result = optimize_menu([], vegan_items, [], constraints)
    assert result["status"] == "Optimal"
    categories = [entry["item"].category for entry in result["items"]]
    assert "Main Course" in categories, "Dinner for 2 must include a Main Course"


def test_preferred_category_strictly_enforces_category():
    """Verify that specifying preferred_categories strictly mandates that category in the cart."""
    sides = [create_mock_item("Sweet Potato Wedges", "Side", 160.0, "Vegan", 1, 4.0)]
    drinks = [create_mock_item("Oat Milk Latte", "Beverage", 180.0, "Vegan", 1, 4.0)]
    desserts = [create_mock_item("Cacao Truffles", "Dessert", 190.0, "Vegan", 1, 4.0)]
    mains = [create_mock_item("Vegan Pesto Pasta", "Main Course", 340.0, "Vegan", 1, 4.0)]

    vegan_items = sides + drinks + desserts + mains
    constraints = ExtractedConstraints(
        people_count=2,
        vegetarian_count=0,
        vegan_count=2,
        non_vegetarian_count=0,
        max_budget=1000.0,
        preferred_categories=["Main Course"],
        excluded_dishes=["Green Juice"],
    )
    result = optimize_menu([], vegan_items, [], constraints)
    assert result["status"] == "Optimal"
    categories = [entry["item"].category for entry in result["items"]]
    assert "Main Course" in categories
    assert any(entry["item"].name == "Vegan Pesto Pasta" for entry in result["items"])


def test_anti_monopoly_caps_on_beverages_and_sides():
    """Verify that beverages and sides are capped so peripheral items cannot flood the cart."""
    drinks = [
        create_mock_item("Drink A", "Beverage", 50.0, "Vegan", 1, 5.0),
        create_mock_item("Drink B", "Beverage", 50.0, "Vegan", 1, 5.0),
    ]
    sides = [
        create_mock_item("Side A", "Side", 50.0, "Vegan", 1, 5.0),
        create_mock_item("Side B", "Side", 50.0, "Vegan", 1, 5.0),
    ]
    mains = [create_mock_item("Main A", "Main Course", 200.0, "Vegan", 1, 4.0)]

    vegan_items = drinks + sides + mains
    constraints = ExtractedConstraints(
        people_count=2,
        vegetarian_count=0,
        vegan_count=2,
        non_vegetarian_count=0,
        max_budget=1000.0,
    )
    result = optimize_menu([], vegan_items, [], constraints)
    assert result["status"] == "Optimal"
    total_drinks = sum(entry["quantity"] for entry in result["items"] if entry["item"].category == "Beverage")
    total_sides = sum(entry["quantity"] for entry in result["items"] if entry["item"].category == "Side")
    assert total_drinks <= 2, f"Beverages should not exceed total_people (2), got {total_drinks}"
    assert total_sides <= 1, f"Sides should not exceed ceil(total_people/2) (1), got {total_sides}"


def test_optimizer_heavily_filtered_small_menu_group_order():
    """Verify that a 7-person party can be successfully fed even when strict allergen/cuisine filters leave only 3 items."""
    starter = create_mock_item("Bruschetta", "Starter", 230.0, "Vegan", 1, 4.4)
    main = create_mock_item("Spaghetti Bolognese", "Main Course", 440.0, "Non-Vegetarian", 1, 4.6)
    drink = create_mock_item("Espresso", "Beverage", 120.0, "Vegan", 1, 4.1)

    constraints = ExtractedConstraints(
        people_count=7,
        vegetarian_count=0,
        vegan_count=0,
        non_vegetarian_count=7,
        max_budget=4000.0,
    )
    result = optimize_menu([], [starter, drink], [main], constraints)
    assert result["status"] == "Optimal"
    assert result["total_cost"] <= 4000.0
    assert result["total_servings"] >= 7
    categories = set(entry["item"].category for entry in result["items"])
    assert "Starter" in categories
    assert "Main Course" in categories


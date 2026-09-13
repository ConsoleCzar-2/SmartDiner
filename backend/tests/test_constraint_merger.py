from app.schemas.constraints import ExtractedConstraints
from app.services.constraint_merger import merge_constraints

def test_basic_merge():
    existing = {
        "people_count": 2,
        "max_budget": 1000.0,
        "excluded_allergens": ["Dairy"],
        "max_spice_level": "Medium"
    }
    
    # Delta: Add 1 person, keep everything else same (by leaving null/empty)
    delta = ExtractedConstraints(
        people_count=3,
        is_modification=True
    )
    
    merged = merge_constraints(existing, delta)
    
    assert merged.people_count == 3
    assert merged.max_budget == 1000.0
    assert merged.excluded_allergens == ["Dairy"]
    assert merged.max_spice_level == "Medium"
    assert merged.is_modification == True

def test_auto_compute_nonveg():
    existing = {}
    delta = ExtractedConstraints(
        people_count=4,
        vegetarian_count=1,
        vegan_count=1
    )
    
    merged = merge_constraints(existing, delta)
    assert merged.non_vegetarian_count == 2
    
def test_invariant_validation_people_count():
    existing = {"people_count": 2}
    
    # If the user says "add 2 vegans, 1 veg" and delta brings total to 3
    # The merger should bump people_count to at least 3
    delta = ExtractedConstraints(
        vegan_count=2,
        vegetarian_count=1
    )
    
    merged = merge_constraints(existing, delta)
    assert merged.people_count == 3 # 2+1
    assert merged.non_vegetarian_count == 0

def test_list_overwrite():
    existing = {
        "preferred_categories": ["Starter", "Main Course"]
    }
    
    delta = ExtractedConstraints(
        preferred_categories=["Dessert"]
    )
    
    merged = merge_constraints(existing, delta)
    assert merged.preferred_categories == ["Dessert"]

def test_merge_category_min_counts_and_dish_quantities():
    existing = {
        "category_min_counts": {"Starter": 1},
        "dish_quantities": {"Paneer Tikka": 1},
        "preferred_categories": ["Starter"]
    }
    
    delta = ExtractedConstraints(
        category_min_counts={"Bread": 2, "Beverage": 2},
        dish_quantities={"Garlic Naan": 2, "Masala Kadak Chai": 2},
        is_modification=True
    )
    
    merged = merge_constraints(existing, delta)
    assert merged.category_min_counts["Starter"] == 1
    assert merged.category_min_counts["Bread"] == 2
    assert merged.category_min_counts["Beverage"] == 2
    assert merged.dish_quantities["Garlic Naan"] == 2
    assert merged.dish_quantities["Masala Kadak Chai"] == 2
    assert "Bread" in merged.preferred_categories
    assert "Beverage" in merged.preferred_categories
    assert "Garlic Naan" in merged.specific_dish_requests

def test_excluded_dishes_pruning():
    existing = {
        "dish_quantities": {"Garlic Naan": 2, "Paneer Tikka": 1},
        "specific_dish_requests": ["Garlic Naan", "Paneer Tikka"]
    }
    
    delta = ExtractedConstraints(
        excluded_dishes=["Paneer Tikka"],
        is_modification=True
    )
    
    merged = merge_constraints(existing, delta)
    assert "Paneer Tikka" not in merged.dish_quantities
    assert "Paneer Tikka" not in merged.specific_dish_requests
    assert merged.dish_quantities["Garlic Naan"] == 2


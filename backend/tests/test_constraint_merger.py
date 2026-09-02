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

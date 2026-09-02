from app.schemas.constraints import ExtractedConstraints

def merge_constraints(existing: dict, delta: ExtractedConstraints) -> ExtractedConstraints:
    """
    Merges the newly extracted constraint delta into the existing constraint state.
    - Numeric/String fields: overwritten if delta provides a non-default/non-null value.
    - List fields: replaced entirely if delta provides them (the LLM is instructed to output the full list if it changes).
    - non_vegetarian_count is auto-computed as (people_count - vegetarian_count - vegan_count).
    """
    # Start with a copy of existing state
    merged = dict(existing) if existing else {}
    
    delta_dict = delta.model_dump(exclude_unset=True)
    
    # 1. Merge explicitly provided scalar/string fields
    for field in ["people_count", "max_budget", "max_spice_level", "is_modification"]:
        if field in delta_dict and delta_dict[field] is not None:
            # Special case for max_spice_level: only override if not "Any" OR if it wasn't set
            if field == "max_spice_level" and delta_dict[field] == "Any" and merged.get(field, "Any") != "Any":
                pass # Keep existing specific spice level
            else:
                merged[field] = delta_dict[field]
                
    # Merge dietary counts
    for field in ["vegetarian_count", "vegan_count"]:
        if field in delta_dict and delta_dict[field] is not None:
            merged[field] = delta_dict[field]
            
    # 2. Merge list fields (LLM outputs full new lists for these if they change, else empty)
    for list_field in ["excluded_allergens", "preferred_cuisines", "preferred_categories", "specific_dish_requests", "excluded_dishes"]:
        if list_field in delta_dict and len(delta_dict[list_field]) > 0:
            # If the user says "remove X", the LLM is instructed to output the final merged list,
            # so we just overwrite the existing list with the LLM's list.
            merged[list_field] = delta_dict[list_field]

    # Ensure people_count defaults to at least 1
    people = merged.get("people_count", 1)
    if people < 1:
        people = 1
    merged["people_count"] = people
    
    # 3. Invariant validation & Math
    veg = merged.get("vegetarian_count", 0)
    vegan = merged.get("vegan_count", 0)
    
    if veg + vegan > people:
        # If user added more veg/vegan than people, bump up people_count
        merged["people_count"] = veg + vegan
        people = merged["people_count"]
        
    # Auto-compute non-veg
    merged["non_vegetarian_count"] = people - veg - vegan
    
    # Parse back to Pydantic
    return ExtractedConstraints(**merged)

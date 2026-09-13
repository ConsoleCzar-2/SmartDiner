from app.schemas.constraints import ExtractedConstraints

def merge_constraints(existing: dict, delta: ExtractedConstraints) -> ExtractedConstraints:
    """
    Merges the newly extracted constraint delta into the existing constraint state.
    - Numeric/String fields: overwritten if delta provides a non-default/non-null value.
    - List fields: replaced entirely if delta provides them (the LLM is instructed to output the full list if it changes).
    - Dictionary fields (category_min_counts, dish_quantities): merged and updated.
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

    # 3. Merge dictionary quantity fields
    for dict_field in ["category_min_counts", "dish_quantities"]:
        if dict_field in delta_dict and delta_dict[dict_field]:
            curr_dict = dict(merged.get(dict_field, {}) or {})
            for k, v in delta_dict[dict_field].items():
                if v is not None and v > 0:
                    curr_dict[k] = v
                elif v == 0 and k in curr_dict:
                    del curr_dict[k]
            merged[dict_field] = curr_dict

    # Cross-field consistency: category_min_counts reflected in preferred_categories
    if merged.get("category_min_counts"):
        pref_cats = set(merged.get("preferred_categories", []) or [])
        for cat, cnt in merged["category_min_counts"].items():
            if cnt > 0:
                pref_cats.add(cat)
        merged["preferred_categories"] = list(pref_cats)

    # Cross-field consistency: dish_quantities reflected in specific_dish_requests
    if merged.get("dish_quantities"):
        spec_dishes = list(merged.get("specific_dish_requests", []) or [])
        for dish, cnt in merged["dish_quantities"].items():
            if cnt > 0 and not any(dish.lower() == sd.lower() for sd in spec_dishes):
                spec_dishes.append(dish)
        merged["specific_dish_requests"] = spec_dishes

    # Excluded dishes clean-up from dish_quantities and specific_dish_requests
    if merged.get("excluded_dishes"):
        excl_lower = set(d.lower() for d in merged["excluded_dishes"])
        if "dish_quantities" in merged and merged["dish_quantities"]:
            merged["dish_quantities"] = {k: v for k, v in merged["dish_quantities"].items() if k.lower() not in excl_lower}
        if "specific_dish_requests" in merged and merged["specific_dish_requests"]:
            merged["specific_dish_requests"] = [d for d in merged["specific_dish_requests"] if d.lower() not in excl_lower]

    # Ensure people_count defaults to at least 1
    people = merged.get("people_count", 1)
    if people < 1:
        people = 1
    merged["people_count"] = people
    
    # 4. Invariant validation & Math
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


import math
import pulp
from app.schemas.constraints import ExtractedConstraints
from app.models.menu_item import MenuItem

def optimize_menu(veg_items: list[MenuItem], vegan_items: list[MenuItem], 
                  nonveg_items: list[MenuItem], constraints: ExtractedConstraints) -> dict:
    """
    Uses Integer Linear Programming (ILP) to find the optimal combination of menu items.
    Maximizes rating & serving efficiency while strictly obeying budget and dietary constraints.
    """
    prob = pulp.LpProblem("RestaurantMenuOptimization", pulp.LpMaximize)
    
    all_items = veg_items + vegan_items + nonveg_items
    if not all_items:
        return {
            "status": "Infeasible", 
            "reason": "No items available after filtering constraints (like allergens or strict cuisines).", 
            "items": [], 
            "total_cost": 0.0, 
            "total_servings": 0
        }

    total_people = constraints.people_count or 1
    max_qty_per_dish = max(2, math.ceil(total_people / 3.0))

    # Calculate available categories
    available_categories = len(set(item.category for item in all_items))
    min_categories = min(available_categories, max(2, math.ceil(total_people / 2.0)))

    # --- 1. Decision Variables ---
    item_vars = {}
    category_vars = {}
    
    for item in all_items:
        safe_id = str(item.id).replace("-", "_")
        var = pulp.LpVariable(f"qty_{safe_id}", lowBound=0, upBound=max_qty_per_dish, cat='Integer')
        item_vars[item.id] = var
        
    for cat in set(item.category for item in all_items):
        safe_cat = cat.replace(" ", "_").replace("-", "_")
        c_var = pulp.LpVariable(f"cat_{safe_cat}", cat='Binary')
        category_vars[cat] = c_var
        
        # Link item vars to category vars (Big-M method)
        cat_items = [item for item in all_items if item.category == cat]
        M = max_qty_per_dish * len(cat_items)
        prob += pulp.lpSum([item_vars[i.id] for i in cat_items]) <= M * c_var, f"LinkCat_{safe_cat}"

    # --- 2. Objective Function ---
    # Maximize: SUM(Quantity * Rating * Serving Size) + Bonus for category diversity
    prob += pulp.lpSum([item_vars[item.id] * float(item.rating) * item.serving_size for item in all_items]) + pulp.lpSum([3.0 * c_var for c_var in category_vars.values()])

    # --- 3. Hard Constraints ---
    
    # A. Budget
    if constraints.max_budget:
        prob += pulp.lpSum([item_vars[item.id] * float(item.price) for item in all_items]) <= float(constraints.max_budget), "BudgetConstraint"
        
    # B. Minimum Total Servings
    prob += pulp.lpSum([item_vars[item.id] * item.serving_size for item in all_items]) >= total_people, "TotalServingsConstraint"
    
    # C. Dietary Separation & Servings
    veg_people = constraints.vegetarian_count or 0
    vegan_people = constraints.vegan_count or 0
    nonveg_people = constraints.non_vegetarian_count or 0
    
    if veg_people > 0:
        prob += pulp.lpSum([item_vars[item.id] * item.serving_size for item in (veg_items + vegan_items)]) >= veg_people, "VegServingsConstraint"

    if vegan_people > 0:
        prob += pulp.lpSum([item_vars[item.id] * item.serving_size for item in vegan_items]) >= vegan_people, "VeganServingsConstraint"

    if nonveg_people > 0:
        prob += pulp.lpSum([item_vars[item.id] * item.serving_size for item in nonveg_items]) >= nonveg_people, "NonVegServingsConstraint"
    else:
        # HARD GUARDRAIL: If 0 non-veg people, force non-veg items to 0
        for item in nonveg_items:
            prob += item_vars[item.id] == 0, f"ForceZeroNonVeg_{str(item.id).replace('-', '_')}"
            
    # Upper bounds to prevent over-ordering specific dietary types when not needed
    if nonveg_people > 0:
        prob += pulp.lpSum([item_vars[item.id] * item.serving_size for item in nonveg_items]) <= nonveg_people * 4, "MaxNonVegServings"
    
    if veg_people + vegan_people > 0:
        prob += pulp.lpSum([item_vars[item.id] * item.serving_size for item in (veg_items + vegan_items)]) <= (veg_people + vegan_people) * 4, "MaxVegServings"

    # D. Maximum Total Servings (Feast Limit)
    prob += pulp.lpSum([item_vars[item.id] * item.serving_size for item in all_items]) <= total_people * 4, "MaxServingsConstraint"
    
    # E. Category Diversity
    prob += pulp.lpSum([c_var for c_var in category_vars.values()]) >= min_categories, "MinCategoryDiversity"

    # F. Specific Dish Requests (Substring Matching)
    if constraints.specific_dish_requests:
        for req_dish in constraints.specific_dish_requests:
            req_dish_lower = req_dish.lower()
            matched_items = [item for item in all_items if req_dish_lower in item.name.lower()]
            if matched_items:
                # Force at least 1 of the matched items to be selected
                prob += pulp.lpSum([item_vars[i.id] for i in matched_items]) >= 1, f"SpecificDish_{req_dish_lower.replace(' ', '_')[:20]}"

    # G. Excluded Dishes
    if constraints.excluded_dishes:
        for excl_dish in constraints.excluded_dishes:
            excl_dish_lower = excl_dish.lower()
            matched_items = [item for item in all_items if excl_dish_lower in item.name.lower()]
            for matched in matched_items:
                prob += item_vars[matched.id] == 0, f"ExcludeDish_{str(matched.id).replace('-', '_')}"

    # H. Preferred Categories
    if constraints.preferred_categories:
        for p_cat in constraints.preferred_categories:
            if p_cat in category_vars:
                # Force the binary variable for this category to be 1
                prob += category_vars[p_cat] >= 1, f"PrefCategory_{p_cat.replace(' ', '_')}"

    # --- 4. Solve ---
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    status_str = pulp.LpStatus[prob.status]
    rationale = {
        "objective": "Maximize SUM(Qty * Rating * Serving Size) + Category Diversity Bonus",
        "budget_limit": float(constraints.max_budget) if constraints.max_budget else "None",
        "min_total_servings": total_people,
        "max_servings_cap": total_people * 4,
        "min_categories": min_categories,
        "veg_people": constraints.vegetarian_count or 0,
        "vegan_people": constraints.vegan_count or 0,
        "nonveg_people": constraints.non_vegetarian_count or 0,
        "specific_dishes_matched": len(constraints.specific_dish_requests) if constraints.specific_dish_requests else 0,
        "excluded_dishes_enforced": len(constraints.excluded_dishes) if constraints.excluded_dishes else 0
    }

    if status_str != "Optimal":
        return {
            "status": status_str,
            "reason": "Could not find a mathematically possible combination. The budget might be too tight, or conflicting dietary/specific dish requests.",
            "items": [],
            "total_cost": 0.0,
            "total_servings": 0,
            "decision_rationale": rationale
        }

    selected_items = []
    total_cost = 0.0
    total_servings = 0
    
    for item in all_items:
        qty = int(pulp.value(item_vars[item.id]) or 0)
        if qty > 0:
            subtotal = float(item.price) * qty
            selected_items.append({
                "item": item,
                "quantity": qty,
                "subtotal": subtotal
            })
            total_cost += subtotal
            total_servings += item.serving_size * qty

    selected_items.sort(key=lambda x: x["subtotal"], reverse=True)

    return {
        "status": "Optimal",
        "reason": "Successfully generated an optimal menu within all constraints.",
        "items": selected_items,
        "total_cost": round(total_cost, 2),
        "total_servings": total_servings,
        "decision_rationale": rationale
    }

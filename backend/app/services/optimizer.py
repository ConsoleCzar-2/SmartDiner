import math
import time
import pulp
from app.schemas.constraints import ExtractedConstraints
from app.models.menu_item import MenuItem
def dish_matches(query: str, item_name: str) -> bool:
    """
    Case-insensitive, plural-tolerant matching for dish names.
    E.g. 'chicken dim sums' -> 'Chicken Dim Sum Basket'
         'parottas' -> 'Malabar Parotta (2 pcs)'
         'noodles' -> 'Veg Hakka Noodles'
    """
    q = query.lower().strip()
    name = item_name.lower().strip()
    if not q or not name:
        return False
    if q in name or name in q:
        return True

    def stem(w: str) -> str:
        w = w.rstrip("s")
        if w.endswith("ie"):
            w = w[:-2] + "y"
        return w

    q_tokens = [stem(w) for w in q.split() if len(w) > 2]
    name_tokens = [stem(w) for w in name.split() if len(w) > 2]
    if q_tokens and all(any(qt == nt or qt in nt for nt in name_tokens) for qt in q_tokens):
        return True
    return False

def optimize_menu(veg_items: list[MenuItem], vegan_items: list[MenuItem], 
                  nonveg_items: list[MenuItem], constraints: ExtractedConstraints) -> dict:
    """
    Uses Integer Linear Programming (ILP) to find the optimal combination of menu items.
    Maximizes rating & serving efficiency while strictly obeying budget and dietary constraints,
    with soft penalties for meal course diversity (Starter, Main Course, Dessert/Beverage).
    """
    t0 = time.perf_counter()
    prob = pulp.LpProblem("RestaurantMenuOptimization", pulp.LpMaximize)
    
    all_items = veg_items + vegan_items + nonveg_items
    if not all_items:
        return {
            "status": "Infeasible", 
            "reason": "No items available after filtering constraints (like allergens or strict cuisines).", 
            "items": [], 
            "total_cost": 0.0, 
            "total_servings": 0,
            "decision_rationale": {
                "items_considered": 0,
                "items_selected": 0,
                "solve_time_ms": 0.0
            }
        }

    total_people = constraints.people_count or 1
    # Adjust max_qty_per_dish dynamically based on available menu diversity
    div = min(max(1, len(all_items)), 3.0)
    max_qty_per_dish = max(2, math.ceil(total_people / div))

    veg_people = constraints.vegetarian_count or 0
    vegan_people = constraints.vegan_count or 0
    nonveg_people = constraints.non_vegetarian_count or 0

    if veg_people == 0 and nonveg_people == 0 and vegan_people > 0:
        eligible_items = vegan_items
    elif nonveg_people == 0 and (veg_people > 0 or vegan_people > 0):
        eligible_items = veg_items + vegan_items
    else:
        eligible_items = all_items

    # Calculate available categories from items eligible for this party's diet
    available_categories = len(set(item.category for item in eligible_items))
    target_categories = 1 if total_people == 1 else max(2, math.ceil(total_people / 2.0))
    min_categories = min(available_categories, target_categories)

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
        
        # Link item vars to category vars (Big-M method with bidirectional constraint)
        cat_items = [item for item in all_items if item.category == cat]
        M = max_qty_per_dish * len(cat_items)
        prob += pulp.lpSum([item_vars[i.id] for i in cat_items]) <= M * c_var, f"LinkCatMax_{safe_cat}"
        prob += pulp.lpSum([item_vars[i.id] for i in cat_items]) >= c_var, f"LinkCatMin_{safe_cat}"

    # Soft meal structure penalties (for balanced full meal)
    penalties = []
    starter_items = [i for i in all_items if i.category == "Starter"]
    main_items = [i for i in all_items if i.category == "Main Course"]
    sweet_drink_items = [i for i in all_items if i.category in ("Dessert", "Beverage")]

    # For strictly vegan groups, restrict the main_items considered for structure to vegan
    if veg_people == 0 and nonveg_people == 0 and vegan_people > 0:
        main_items = [i for i in main_items if i.dietary_preference == "Vegan"]
    elif nonveg_people == 0 and (veg_people > 0 or vegan_people > 0):
        main_items = [i for i in main_items if i.dietary_preference in ("Vegetarian", "Vegan")]

    # Every meal should prioritize a Main Course if available
    if main_items:
        slack_main = pulp.LpVariable("slack_main", cat='Binary')
        prob += pulp.lpSum([item_vars[i.id] for i in main_items]) >= 1 - slack_main, "SoftMainReq"
        penalties.append(30.0 * slack_main)

    if total_people >= 3:
        if starter_items:
            slack_starter = pulp.LpVariable("slack_starter", cat='Binary')
            prob += pulp.lpSum([item_vars[i.id] for i in starter_items]) >= 1 - slack_starter, "SoftStarterReq"
            penalties.append(10.0 * slack_starter)

        if sweet_drink_items:
            slack_sweet = pulp.LpVariable("slack_sweet", cat='Binary')
            prob += pulp.lpSum([item_vars[i.id] for i in sweet_drink_items]) >= 1 - slack_sweet, "SoftSweetDrinkReq"
            penalties.append(5.0 * slack_sweet)

    # --- 2. Objective Function ---
    # Maximize: SUM(Quantity * Rating * Serving Size) + Bonus for category diversity (increased to 5.0) - Soft Penalties
    base_objective = pulp.lpSum([item_vars[item.id] * float(item.rating) * item.serving_size for item in all_items])
    diversity_bonus = pulp.lpSum([5.0 * c_var for c_var in category_vars.values()])
    penalty_deduction = pulp.lpSum(penalties) if penalties else 0.0

    prob += base_objective + diversity_bonus - penalty_deduction

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

    max_nonveg_cap = sum(max_qty_per_dish * item.serving_size for item in nonveg_items)
    req_nonveg = min(nonveg_people, max_nonveg_cap)

    if req_nonveg > 0:
        prob += pulp.lpSum([item_vars[item.id] * item.serving_size for item in nonveg_items]) >= req_nonveg, "NonVegServingsConstraint"
    elif (veg_people > 0 or vegan_people > 0) and nonveg_people == 0:
        # HARD GUARDRAIL: Only force non-veg items to 0 if the party explicitly requested veg/vegan and 0 non-veg
        for item in nonveg_items:
            prob += item_vars[item.id] == 0, f"ForceZeroNonVeg_{str(item.id).replace('-', '_')}"

    if veg_people == 0 and nonveg_people == 0 and vegan_people > 0:
        # HARD GUARDRAIL: If 0 veg and 0 non-veg people (strictly vegan party), force vegetarian items to 0
        for item in veg_items:
            prob += item_vars[item.id] == 0, f"ForceZeroVeg_{str(item.id).replace('-', '_')}"
            
    # Upper bounds to prevent over-ordering specific dietary types when not needed
    if nonveg_people > 0:
        prob += pulp.lpSum([item_vars[item.id] * item.serving_size for item in nonveg_items]) <= nonveg_people * 4, "MaxNonVegServings"
    
    if veg_people + vegan_people > 0:
        prob += pulp.lpSum([item_vars[item.id] * item.serving_size for item in (veg_items + vegan_items)]) <= (veg_people + vegan_people) * 4, "MaxVegServings"

    if veg_people > 0 and vegan_people > 0:
        prob += pulp.lpSum([item_vars[item.id] * item.serving_size for item in veg_items]) <= veg_people * 4, "MaxPureVegServings"

    # D. Maximum Total Servings (Feast Limit)
    prob += pulp.lpSum([item_vars[item.id] * item.serving_size for item in all_items]) <= total_people * 4, "MaxServingsConstraint"
    
    # E. Category Diversity
    prob += pulp.lpSum([c_var for c_var in category_vars.values()]) >= min_categories, "MinCategoryDiversity"

    # Anti-monopoly caps for Bread and Rice to prevent carbohydrate-only carts
    bread_items = [i for i in all_items if i.category == "Bread"]
    if bread_items:
        max_bread = max(2, math.ceil(total_people / 2.0))
        prob += pulp.lpSum([item_vars[i.id] for i in bread_items]) <= max_bread, "MaxBreadCap"

    rice_items = [i for i in all_items if i.category == "Rice"]
    if rice_items:
        max_rice = max(1, math.ceil(total_people / 2.0))
        prob += pulp.lpSum([item_vars[i.id] for i in rice_items]) <= max_rice, "MaxRiceCap"

    # Anti-monopoly caps for Beverage, Side, and Dessert to prevent peripheral items from dominating meals
    pref_cats = set(constraints.preferred_categories or [])

    beverage_items = [i for i in all_items if i.category == "Beverage"]
    if beverage_items and "Beverage" not in pref_cats:
        max_bev = max(1, total_people)
        prob += pulp.lpSum([item_vars[i.id] for i in beverage_items]) <= max_bev, "MaxBeverageCap"

    side_items = [i for i in all_items if i.category == "Side"]
    if side_items and "Side" not in pref_cats:
        max_side = max(1, math.ceil(total_people / 2.0))
        prob += pulp.lpSum([item_vars[i.id] for i in side_items]) <= max_side, "MaxSideCap"

    dessert_items = [i for i in all_items if i.category == "Dessert"]
    if dessert_items and "Dessert" not in pref_cats:
        max_dessert = max(1, math.ceil(total_people / 2.0))
        prob += pulp.lpSum([item_vars[i.id] for i in dessert_items]) <= max_dessert, "MaxDessertCap"

    # F. Specific Dish Requests (Substring & Plural-Tolerant Matching)
    if constraints.specific_dish_requests:
        for req_dish in constraints.specific_dish_requests:
            matched_items = [item for item in all_items if dish_matches(req_dish, item.name)]
            if matched_items:
                dish_label = req_dish.lower().replace(' ', '_')[:20]
                prob += pulp.lpSum([item_vars[i.id] for i in matched_items]) >= 1, f"SpecificDish_{dish_label}"

    # G. Excluded Dishes
    if constraints.excluded_dishes:
        for excl_dish in constraints.excluded_dishes:
            matched_items = [item for item in all_items if dish_matches(excl_dish, item.name)]
            for matched in matched_items:
                prob += item_vars[matched.id] == 0, f"ExcludeDish_{str(matched.id).replace('-', '_')}"

    # H. Preferred Categories (strictly enforce at least 1 dish from requested categories)
    if constraints.preferred_categories:
        for p_cat in constraints.preferred_categories:
            cat_dishes = [item for item in all_items if item.category == p_cat]
            if veg_people == 0 and nonveg_people == 0 and vegan_people > 0:
                cat_dishes = [item for item in cat_dishes if item.dietary_preference == "Vegan"]
            elif nonveg_people == 0 and (veg_people > 0 or vegan_people > 0):
                cat_dishes = [item for item in cat_dishes if item.dietary_preference in ("Vegetarian", "Vegan")]

            if cat_dishes:
                safe_cat = p_cat.replace(" ", "_").replace("-", "_")
                prob += pulp.lpSum([item_vars[i.id] for i in cat_dishes]) >= 1, f"ReqPrefCat_{safe_cat}"
            elif p_cat in category_vars:
                prob += category_vars[p_cat] >= 1, f"PrefCategory_{p_cat.replace(' ', '_')}"

    # --- 4. Solve ---
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    t1 = time.perf_counter()
    solve_time_ms = round((t1 - t0) * 1000, 2)

    status_str = pulp.LpStatus[prob.status]
    obj_val = round(float(pulp.value(prob.objective) or 0.0), 2) if prob.status == 1 else 0.0

    rationale = {
        "objective": "Maximize SUM(Qty * Rating * Serving Size) + Category Diversity Bonus (5.0) - Meal Structure Penalties",
        "objective_value": obj_val,
        "solve_time_ms": solve_time_ms,
        "items_considered": len(all_items),
        "items_selected": 0,
        "categories_activated": [],
        "budget_limit": float(constraints.max_budget) if constraints.max_budget else "None",
        "min_total_servings": total_people,
        "max_servings_cap": total_people * 4,
        "min_categories": min_categories,
        "veg_people": constraints.vegetarian_count or 0,
        "vegan_people": constraints.vegan_count or 0,
        "nonveg_people": constraints.non_vegetarian_count or 0,
        "constraint_actuals": {}
    }

    if status_str != "Optimal":
        if len(all_items) < min_categories:
            diag_reason = f"Only {len(all_items)} dish(es) matched your filters, but at least {min_categories} categories were required."
        elif constraints.max_budget and float(constraints.max_budget) < 150 * total_people:
            diag_reason = "The specified budget appears too tight to satisfy the group size."
        else:
            diag_reason = "Strict filtering (allergens, spice ceiling, cuisine) left too few eligible dishes to satisfy meal courses and group portions."
        return {
            "status": status_str,
            "reason": diag_reason,
            "items": [],
            "total_cost": 0.0,
            "total_servings": 0,
            "decision_rationale": rationale
        }

    selected_items = []
    total_cost = 0.0
    total_servings = 0
    actual_veg_servings = 0
    actual_nonveg_servings = 0
    active_categories = set()
    
    for item in all_items:
        qty = int(pulp.value(item_vars[item.id]) or 0)
        if qty > 0:
            subtotal = float(item.price) * qty
            servings = item.serving_size * qty
            selected_items.append({
                "item": item,
                "quantity": qty,
                "subtotal": subtotal
            })
            total_cost += subtotal
            total_servings += servings
            active_categories.add(item.category)
            if item.dietary_preference in ("Vegetarian", "Vegan"):
                actual_veg_servings += servings
            else:
                actual_nonveg_servings += servings

    selected_items.sort(key=lambda x: x["subtotal"], reverse=True)
    activated_cat_list = sorted(list(active_categories))

    rationale["items_selected"] = len(selected_items)
    rationale["categories_activated"] = activated_cat_list
    rationale["constraint_actuals"] = {
        "budget": {
            "limit": float(constraints.max_budget) if constraints.max_budget else None,
            "used": round(total_cost, 2)
        },
        "total_servings": {
            "floor": total_people,
            "cap": total_people * 4,
            "actual": total_servings
        },
        "veg_servings": {
            "floor": veg_people,
            "actual": actual_veg_servings
        },
        "nonveg_servings": {
            "floor": nonveg_people,
            "actual": actual_nonveg_servings
        },
        "categories": {
            "required": min_categories,
            "delivered": len(activated_cat_list)
        }
    }

    return {
        "status": "Optimal",
        "reason": "Successfully generated an optimal menu within all constraints.",
        "items": selected_items,
        "total_cost": round(total_cost, 2),
        "total_servings": total_servings,
        "decision_rationale": rationale
    }

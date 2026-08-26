import math
import pulp
from app.schemas.constraints import ExtractedConstraints
from app.models.menu_item import MenuItem

def optimize_menu(veg_items: list[MenuItem], nonveg_items: list[MenuItem], constraints: ExtractedConstraints) -> dict:
    """
    Uses Integer Linear Programming (ILP) to find the optimal combination of menu items.
    Maximizes rating & serving efficiency while strictly obeying budget and dietary constraints.
    """
    prob = pulp.LpProblem("RestaurantMenuOptimization", pulp.LpMaximize)
    
    all_items = veg_items + nonveg_items
    if not all_items:
        return {
            "status": "Infeasible", 
            "reason": "No items available after filtering constraints (like allergens or strict cuisines).", 
            "items": [], 
            "total_cost": 0.0, 
            "total_servings": 0
        }

    # --- 1. Dynamic Diversity Cap ---
    total_people = constraints.people_count or 1
    # max_qty scales dynamically: max 2 for tiny groups, larger caps for big groups.
    max_qty_per_dish = max(2, math.ceil(total_people / 3.0))

    # --- 2. Decision Variables ---
    item_vars = {}
    for item in all_items:
        # id is a UUID object, stringify it for the variable name
        safe_id = str(item.id).replace("-", "_")
        # Ensure quantity is >= 0, integer, and <= max_qty_per_dish
        var = pulp.LpVariable(f"qty_{safe_id}", lowBound=0, upBound=max_qty_per_dish, cat='Integer')
        item_vars[item.id] = var

    # --- 3. Objective Function ---
    # Maximize: SUM(Quantity * Rating * Serving Size)
    # We want highly rated food that provides good value (feeds people).
    prob += pulp.lpSum([item_vars[item.id] * float(item.rating) * item.serving_size for item in all_items])

    # --- 4. Hard Constraints ---
    
    # A. Budget (Absolute guarantee)
    if constraints.max_budget:
        prob += pulp.lpSum([item_vars[item.id] * float(item.price) for item in all_items]) <= float(constraints.max_budget), "BudgetConstraint"
        
    # B. Total Servings (Ensure everyone eats)
    prob += pulp.lpSum([item_vars[item.id] * item.serving_size for item in all_items]) >= total_people, "TotalServingsConstraint"
    
    # C. Vegetarian Servings (Ensure vegetarians have enough food specifically for them)
    veg_people = constraints.vegetarian_count or 0
    if veg_people > 0:
        if not veg_items:
            return {
                "status": "Infeasible",
                "reason": "No vegetarian items left after filtering, but vegetarians are present.",
                "items": [],
                "total_cost": 0.0,
                "total_servings": 0
            }
        prob += pulp.lpSum([item_vars[item.id] * item.serving_size for item in veg_items]) >= veg_people, "VegServingsConstraint"

    # --- 5. Solve the Problem ---
    # Disable logs so it doesn't spam the console during API requests
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    # --- 6. Parse Output ---
    status_str = pulp.LpStatus[prob.status]
    if status_str != "Optimal":
        return {
            "status": status_str,
            "reason": "Could not find a mathematically possible combination. The budget might be too tight, or you requested too much food for too little money.",
            "items": [],
            "total_cost": 0.0,
            "total_servings": 0
        }

    selected_items = []
    total_cost = 0.0
    total_servings = 0
    
    for item in all_items:
        # value() gets the solved integer value for the variable
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

    # Sort descending by subtotal to put big mains at the top of the list
    selected_items.sort(key=lambda x: x["subtotal"], reverse=True)

    return {
        "status": "Optimal",
        "reason": "Successfully generated an optimal menu within all constraints.",
        "items": selected_items,
        "total_cost": round(total_cost, 2),
        "total_servings": total_servings
    }

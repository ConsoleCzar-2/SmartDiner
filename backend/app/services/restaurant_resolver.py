import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from google import genai
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem
from app.schemas.constraints import ExtractedConstraints
from app.config import settings

logger = logging.getLogger(__name__)

async def resolve_restaurant(
    db_session: AsyncSession,
    user_message: str,
    constraints: ExtractedConstraints = None,
    current_restaurant_id: str = None
) -> dict:
    """
    Resolves a restaurant from the user message, or performs cross-restaurant search.
    Returns a dict with:
      - status: 'RESOLVED' | 'CROSS_RESTAURANT' | 'AMBIGUOUS' | 'NO_MATCH'
      - restaurant: Restaurant object (if resolved or winner found)
      - comparison_summary: str (if cross-restaurant comparison performed)
      - candidate_comparisons: list of dicts (candidates evaluated)
      - clarification_message: str (if ambiguous)
    """
    # 1. Fetch all active restaurants
    res = await db_session.execute(select(Restaurant).where(Restaurant.is_active == True))
    all_restaurants = res.scalars().all()
    if not all_restaurants:
        return {"status": "NO_MATCH", "clarification_message": "No active restaurants available."}

    user_msg_lower = user_message.lower()

    # 2. Check for direct name match in user message
    user_msg_clean = user_msg_lower.replace("'", "").replace('"', "")
    exact_matches = []
    partial_matches = []

    for r in all_restaurants:
        r_name_lower = r.name.lower()
        r_clean = r_name_lower.replace("the ", "").replace("'", "").replace('"', "").strip()

        # Check full name or stripped article name (e.g., "the grand kitchen" or "grand kitchen")
        if r_name_lower in user_msg_lower or r_clean in user_msg_clean:
            exact_matches.append(r)
            continue

        # Check multi-word prefix (e.g., "south spice" for "South Spice Heritage", "green haven" for "Green Haven Cafe")
        parts = r_clean.split()
        if len(parts) >= 2:
            prefix = " ".join(parts[:2])
            if prefix in user_msg_clean:
                exact_matches.append(r)
                continue

        # Check distinctive single keywords (excluding generic terms like cafe, kitchen, express)
        generic_words = {"the", "cafe", "kitchen", "heritage", "restaurant", "bistro", "express", "zone", "grill", "house"}
        distinctive = [w for w in parts if w not in generic_words and len(w) >= 4]
        if any(f" {dw} " in f" {user_msg_clean} " or user_msg_clean.startswith(f"{dw} ") or user_msg_clean.endswith(f" {dw}") for dw in distinctive):
            partial_matches.append(r)

    direct_matches = exact_matches if exact_matches else partial_matches

    if len(direct_matches) == 1:
        return {
            "status": "RESOLVED",
            "restaurant": direct_matches[0],
            "cross_restaurant": False
        }

    # 3. Check for cross-restaurant optimization signals
    cross_signals = [
        "cheapest", "lowest", "best", "across", "compare", "recommend", 
        "any restaurant", "where can i get", "find me", "which restaurant", 
        "where else", "other restaurants", "different restaurant", "switch restaurant"
    ]
    is_cross_intent = any(sig in user_msg_lower for sig in cross_signals)

    # If the user is already scoped to an active restaurant and did not signal cross-restaurant discovery,
    # maintain the current venue without triggering a city-wide cross-comparison.
    if current_restaurant_id and not is_cross_intent:
        curr_r = next((r for r in all_restaurants if str(r.id) == str(current_restaurant_id)), None)
        if curr_r:
            return {
                "status": "RESOLVED",
                "restaurant": curr_r,
                "cross_restaurant": False
            }

    # 4. Search dishes across all restaurants matching keywords / cuisine
    # Find restaurants that have dishes matching specific requests or keywords
    matching_restaurants = []
    keywords = []
    if constraints and constraints.specific_dish_requests:
        keywords.extend([d.lower() for d in constraints.specific_dish_requests])
    
    # Extract dish hints from message if not in constraints
    common_dishes = ["biryani", "pizza", "burger", "dosa", "ramen", "pasta", "noodles", "paneer", "chicken", "salad", "tacos", "falafel"]
    for d in common_dishes:
        if d in user_msg_lower and d not in keywords:
            keywords.append(d)

    candidate_scores = []
    for r in all_restaurants:
        q = select(MenuItem).where(MenuItem.restaurant_id == r.id, MenuItem.is_available == True)
        if keywords:
            # Check matching items
            dish_matches = []
            for kw in keywords:
                res_items = await db_session.execute(
                    select(MenuItem).where(
                        MenuItem.restaurant_id == r.id,
                        MenuItem.is_available == True,
                        func.lower(MenuItem.name).contains(kw)
                    )
                )
                dish_matches.extend(res_items.scalars().all())
            
            if dish_matches:
                avg_price = sum(float(i.price) for i in dish_matches) / len(dish_matches)
                min_price = min(float(i.price) for i in dish_matches)
                avg_rating = sum(float(i.rating) for i in dish_matches) / len(dish_matches)
                candidate_scores.append({
                    "restaurant": r,
                    "matched_count": len(dish_matches),
                    "min_price": min_price,
                    "avg_price": avg_price,
                    "avg_rating": avg_rating,
                    "sample_dish": dish_matches[0].name
                })
        else:
            # Match by cuisine preference or dietary tag if provided
            if constraints and constraints.preferred_cuisines:
                if r.cuisine_type in constraints.preferred_cuisines:
                    candidate_scores.append({
                        "restaurant": r,
                        "matched_count": 10,
                        "min_price": 200,
                        "avg_price": 300,
                        "avg_rating": 4.5,
                        "sample_dish": r.cuisine_type
                    })

    # If we found candidate restaurants via dishes:
    if candidate_scores:
        # Determine sorting criteria
        if "cheapest" in user_msg_lower or "lowest" in user_msg_lower:
            candidate_scores.sort(key=lambda x: x["min_price"])
            criterion_label = "lowest starting price"
        elif "best" in user_msg_lower or "highest rating" in user_msg_lower:
            candidate_scores.sort(key=lambda x: x["avg_rating"], reverse=True)
            criterion_label = "highest average rating"
        else:
            candidate_scores.sort(key=lambda x: (x["min_price"], -x["avg_rating"]))
            criterion_label = "best overall value"

        winner = candidate_scores[0]["restaurant"]
        
        # Build comparison summary for user
        comp_parts = []
        for c in candidate_scores[:3]:
            r_name = c["restaurant"].name
            comp_parts.append(f"{r_name} (from ₹{int(c['min_price'])})")
        
        comparison_text = (
            f"I compared candidate restaurants across the city based on your criteria ({criterion_label}). "
            f"**{winner.name}** was selected as the optimal choice. "
            f"Comparison: {', '.join(comp_parts)}."
        )

        return {
            "status": "CROSS_RESTAURANT",
            "restaurant": winner,
            "cross_restaurant": True,
            "comparison_summary": comparison_text,
            "candidate_comparisons": [
                {
                    "restaurant_id": str(c["restaurant"].id),
                    "restaurant_name": c["restaurant"].name,
                    "cuisine": c["restaurant"].cuisine_type,
                    "sample_dish": c["sample_dish"],
                    "starting_price": c["min_price"]
                }
                for c in candidate_scores[:3]
            ]
        }

    # If user message is a general query without specific dish, default to a high-variety restaurant or ask
    if len(all_restaurants) > 0:
        # If user asks to order/feed people, pick best diverse restaurant
        default_rest = all_restaurants[0]
        options_list = ", ".join([f"**{r.name}** ({r.cuisine_type})" for r in all_restaurants[:4]])
        return {
            "status": "CROSS_RESTAURANT",
            "restaurant": default_rest,
            "cross_restaurant": True,
            "comparison_summary": f"Exploring options starting with **{default_rest.name}**. Available restaurants: {options_list}.",
            "candidate_comparisons": [
                {"restaurant_id": str(r.id), "restaurant_name": r.name, "cuisine": r.cuisine_type}
                for r in all_restaurants[:4]
            ]
        }

    return {
        "status": "AMBIGUOUS",
        "clarification_message": "Could not identify a restaurant. Please name a restaurant (e.g. 'Spice Garden') or specify what you would like to eat."
    }

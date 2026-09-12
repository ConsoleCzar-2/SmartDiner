import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, not_
from sqlalchemy.dialects import postgresql
from app.models.menu_item import MenuItem
from app.models.allergen import Allergen
from app.models.ingredient import MenuItemIngredient, IngredientAllergen
from app.schemas.constraints import ExtractedConstraints
from app.services.optimizer import dish_matches
from app.constants import (
    MENU_FILTER_CACHE_TTL_SECONDS,
    CUISINE_SYNONYMS,
    SPICE_ORDER
)

# In-memory TTL cache for filtered menu queries: key -> (items_dict, query_metadata, timestamp)
MENU_FILTER_CACHE: dict[str, tuple[dict, dict, float]] = {}

def generate_cache_key(restaurant_id: str, constraints: ExtractedConstraints) -> str:
    """Generates a deterministic cache key based on venue and active constraints."""
    allergens = ",".join(sorted(constraints.excluded_allergens or []))
    cuisines = ",".join(sorted(constraints.preferred_cuisines or []))
    spice = constraints.max_spice_level or "Any"
    budget = f"{float(constraints.max_budget):.2f}" if constraints.max_budget is not None else "None"
    req_dishes = ",".join(sorted(constraints.specific_dish_requests or []))
    return f"menu_filter:{restaurant_id}:spice={spice}:allergens={allergens}:cuisines={cuisines}:budget={budget}:dishes={req_dishes}"

def clear_menu_filter_cache(restaurant_id: str = None) -> None:
    """Evicts entries from the in-memory menu filter cache."""
    global MENU_FILTER_CACHE
    if restaurant_id:
        keys_to_remove = [k for k in MENU_FILTER_CACHE if f":{restaurant_id}:" in k]
        for k in keys_to_remove:
            MENU_FILTER_CACHE.pop(k, None)
    else:
        MENU_FILTER_CACHE.clear()

async def filter_menu_items(
    db_session: AsyncSession,
    restaurant_id: str,
    constraints: ExtractedConstraints
) -> tuple[dict, dict]:
    """
    Deterministically filters menu items based on extracted constraints.
    Utilizes an in-memory TTL cache to eliminate redundant database trips.
    Returns (filtered_items_dict, query_metadata_dict).
    """
    t_start = time.perf_counter()
    cache_key = generate_cache_key(restaurant_id, constraints)
    now = time.time()

    # 1. Check in-memory cache
    if cache_key in MENU_FILTER_CACHE:
        cached_items, cached_meta, cache_time = MENU_FILTER_CACHE[cache_key]
        ttl_remaining = MENU_FILTER_CACHE_TTL_SECONDS - (now - cache_time)
        if ttl_remaining > 0:
            retrieval_ms = round((time.perf_counter() - t_start) * 1000, 3)
            # Clone metadata and attach HIT event telemetry
            meta = dict(cached_meta)
            meta["cache_event"] = {
                "cache_type": "IN_MEMORY_MENU_FILTER",
                "key": cache_key,
                "status": "HIT",
                "hit": True,
                "ttl_remaining_s": round(ttl_remaining, 1),
                "duration_ms": retrieval_ms,
                "items_count": len(cached_items.get("all", []))
            }
            return cached_items, meta

    filters_applied = ["restaurant_scope", "availability"]

    # 1. Base Query: Only items from this restaurant that are currently available.
    base_query = select(MenuItem).where(
        and_(
            MenuItem.restaurant_id == restaurant_id,
            MenuItem.is_available == True
        )
    )
    
    # 2. Spice Filter
    if constraints.max_spice_level and constraints.max_spice_level != "Any":
        max_level = SPICE_ORDER.get(constraints.max_spice_level, 4)
        allowed_spice_strings = [k for k, v in SPICE_ORDER.items() if v <= max_level]
        base_query = base_query.where(MenuItem.spice_level.in_(allowed_spice_strings))
        filters_applied.append(f"spice_ceiling:{constraints.max_spice_level}")
    
    # 3. Allergen Exclusion (Safety-Critical)
    if constraints.excluded_allergens:
        allergen_subq = (
            select(MenuItemIngredient.menu_item_id)
            .join(IngredientAllergen, MenuItemIngredient.ingredient_id == IngredientAllergen.ingredient_id)
            .join(Allergen, IngredientAllergen.allergen_id == Allergen.id)
            .where(Allergen.name.in_(constraints.excluded_allergens))
        )
        base_query = base_query.where(~MenuItem.id.in_(allergen_subq))
        filters_applied.append(f"allergen_exclusion:{','.join(constraints.excluded_allergens)}")
    
    # 4. Cuisine Filter
    if constraints.preferred_cuisines:
        cuisines_to_query = set()
        for c in constraints.preferred_cuisines:
            c_clean = c.strip().lower()
            if c_clean in CUISINE_SYNONYMS:
                cuisines_to_query.add(CUISINE_SYNONYMS[c_clean])
            cuisines_to_query.add(c.strip())
        base_query = base_query.where(MenuItem.cuisine.in_(list(cuisines_to_query)))
        filters_applied.append(f"cuisine:{','.join(cuisines_to_query)}")
        
    # 5. Price Ceiling
    if constraints.max_budget:
        base_query = base_query.where(MenuItem.price <= constraints.max_budget)
        filters_applied.append(f"item_price_cap:{constraints.max_budget}")

    # Compile SQL text for audit
    try:
        compiled_sql = str(base_query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    except Exception:
        compiled_sql = str(base_query.compile(dialect=postgresql.dialect()))

    # Execute the query with timing
    t0 = time.perf_counter()
    result = await db_session.execute(base_query)
    all_items = result.scalars().all()
    t1 = time.perf_counter()
    duration_ms = round((t1 - t0) * 1000, 2)

    # If a strict cuisine filter eliminated all items from this restaurant, relax the cuisine constraint
    # while preserving mandatory allergen and spice limits
    if constraints.preferred_cuisines and len(all_items) == 0:
        fallback_query = select(MenuItem).where(
            and_(
                MenuItem.restaurant_id == restaurant_id,
                MenuItem.is_available == True
            )
        )
        if constraints.max_spice_level and constraints.max_spice_level != "Any":
            fallback_query = fallback_query.where(MenuItem.spice_level.in_(allowed_spice_strings))
        if constraints.excluded_allergens:
            fallback_query = fallback_query.where(~MenuItem.id.in_(allergen_subq))
        if constraints.max_budget:
            fallback_query = fallback_query.where(MenuItem.price <= constraints.max_budget)

        fallback_result = await db_session.execute(fallback_query)
        fallback_items = fallback_result.scalars().all()
        if fallback_items:
            all_items = fallback_items
            filters_applied.append("cuisine_relaxed_for_venue")
    
    # Partition the results for the ILP solver
    veg_items = [item for item in all_items if item.dietary_preference == 'Vegetarian']
    vegan_items = [item for item in all_items if item.dietary_preference == 'Vegan']
    nonveg_items = [item for item in all_items if item.dietary_preference == 'Non-Vegetarian']
    
    items_dict = {
        "veg": veg_items,
        "vegan": vegan_items,
        "nonveg": nonveg_items,
        "all": all_items
    }

    # Check for safety conflicts on specific requested dishes
    safety_notes = []
    if constraints.specific_dish_requests and constraints.excluded_allergens:
        allergen_match_q = (
            select(MenuItem.name, Allergen.name)
            .join(MenuItemIngredient, MenuItem.id == MenuItemIngredient.menu_item_id)
            .join(IngredientAllergen, MenuItemIngredient.ingredient_id == IngredientAllergen.ingredient_id)
            .join(Allergen, IngredientAllergen.allergen_id == Allergen.id)
            .where(
                and_(
                    MenuItem.restaurant_id == restaurant_id,
                    MenuItem.is_available == True,
                    Allergen.name.in_(constraints.excluded_allergens)
                )
            )
        )
        conflicts_res = await db_session.execute(allergen_match_q)
        conflicts = conflicts_res.all()
        for req in constraints.specific_dish_requests:
            for item_name, alg_name in conflicts:
                if dish_matches(req, item_name):
                    note = f"Requested dish '{item_name}' was safely excluded because it contains {alg_name}, which violates your strict {alg_name} allergen exclusion."
                    if note not in safety_notes:
                        safety_notes.append(note)

    total_time_ms = round((time.perf_counter() - t_start) * 1000, 2)
    cache_event = {
        "cache_type": "IN_MEMORY_MENU_FILTER",
        "key": cache_key,
        "status": "MISS",
        "hit": False,
        "action": "STORED",
        "ttl_s": MENU_FILTER_CACHE_TTL_SECONDS,
        "duration_ms": duration_ms,
        "total_filter_ms": total_time_ms,
        "items_count": len(all_items)
    }

    query_metadata = {
        "step": "menu_filter",
        "compiled_sql": compiled_sql,
        "filters_applied": filters_applied,
        "rows_returned": len(all_items),
        "duration_ms": duration_ms,
        "safety_notes": safety_notes,
        "cache_event": cache_event
    }

    # Store in cache for future turns or concurrent users
    MENU_FILTER_CACHE[cache_key] = (items_dict, query_metadata, now)

    return items_dict, query_metadata

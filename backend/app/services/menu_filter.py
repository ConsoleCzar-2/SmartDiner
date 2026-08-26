from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, not_
from app.models.menu_item import MenuItem
from app.models.allergen import Allergen
from app.models.ingredient import MenuItemIngredient, IngredientAllergen
from app.schemas.constraints import ExtractedConstraints

async def filter_menu_items(
    db_session: AsyncSession,
    restaurant_id: str,
    constraints: ExtractedConstraints
) -> dict:
    """
    Deterministically filters menu items based on extracted constraints.
    Returns two lists: veg_items and nonveg_items that pass ALL hard filters.
    """
    
    # 1. Base Query: Only items from this restaurant that are currently available.
    base_query = select(MenuItem).where(
        and_(
            MenuItem.restaurant_id == restaurant_id,
            MenuItem.is_available == True
        )
    )
    
    # 2. Spice Filter
    # Map the spice level string to an ordinal integer for easy `<=` filtering.
    if constraints.max_spice_level and constraints.max_spice_level != "Any":
        spice_order = {"None": 0, "Low": 1, "Medium": 2, "High": 3, "Extreme": 4}
        max_level = spice_order.get(constraints.max_spice_level, 4)
        
        # Get all valid spice strings that are <= the max_level
        allowed_spice_strings = [k for k, v in spice_order.items() if v <= max_level]
        base_query = base_query.where(MenuItem.spice_level.in_(allowed_spice_strings))
    
    # 3. Allergen Exclusion (Safety-Critical)
    # If a user excludes "Dairy", we must exclude any dish that contains ANY ingredient
    # that is linked to the "Dairy" allergen.
    if constraints.excluded_allergens:
        # Build the subquery: find menu_item_ids that map to the excluded allergens.
        allergen_subq = (
            select(MenuItemIngredient.menu_item_id)
            .join(IngredientAllergen, MenuItemIngredient.ingredient_id == IngredientAllergen.ingredient_id)
            .join(Allergen, IngredientAllergen.allergen_id == Allergen.id)
            .where(Allergen.name.in_(constraints.excluded_allergens))
        )
        # Exclude those items from the main query
        base_query = base_query.where(~MenuItem.id.in_(allergen_subq))
    
    # 4. Cuisine Filter
    if constraints.preferred_cuisines:
        base_query = base_query.where(MenuItem.cuisine.in_(constraints.preferred_cuisines))
        
    # 5. Price Ceiling
    # Only items that individually cost less than or equal to the total budget.
    if constraints.max_budget:
        base_query = base_query.where(MenuItem.price <= constraints.max_budget)
        
    # Execute the query
    result = await db_session.execute(base_query)
    all_items = result.scalars().all()
    
    # Partition the results for the ILP solver
    veg_items = [item for item in all_items if item.is_veg]
    nonveg_items = [item for item in all_items if not item.is_veg]
    
    return {
        "veg": veg_items,
        "nonveg": nonveg_items,
        "all": all_items
    }

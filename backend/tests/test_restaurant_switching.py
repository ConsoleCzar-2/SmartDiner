import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.restaurant import Restaurant
from app.services.restaurant_resolver import resolve_restaurant

@pytest.mark.asyncio
async def test_restaurant_resolver_exact_and_alias_matches(db_session: AsyncSession):
    """Verify that restaurant resolver accurately matches restaurant names and aliases."""
    
    # 1. Spice Garden
    res1 = await resolve_restaurant(db_session, "Let's get an order for 2 under 2000 from Spice Garden.")
    assert res1["status"] == "RESOLVED"
    assert res1["restaurant"].name == "Spice Garden"

    # 2. Grand Kitchen without leading 'The'
    res2 = await resolve_restaurant(db_session, "Can we get dinner from Grand Kitchen?")
    assert res2["status"] == "RESOLVED"
    assert res2["restaurant"].name == "The Grand Kitchen"

    # 3. Dragons Wok without apostrophe
    res3 = await resolve_restaurant(db_session, "I want something from Dragons Wok tonight")
    assert res3["status"] == "RESOLVED"
    assert res3["restaurant"].name == "Dragon's Wok"

    # 4. South Spice prefix
    res4 = await resolve_restaurant(db_session, "Let's order dosa from South Spice")
    assert res4["status"] == "RESOLVED"
    assert res4["restaurant"].name == "South Spice Heritage"

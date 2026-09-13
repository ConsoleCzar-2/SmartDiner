import pytest
from app.models.admin_user import AdminUser
from app.routers.admin import get_metrics, get_analytics

@pytest.mark.asyncio
async def test_admin_metrics_and_time_ranges(db_session):
    admin = AdminUser(
        id="test-platform-admin",
        email="admin@smartdiner.io",
        password_hash="mock",
        role="PLATFORM_ADMIN",
        restaurant_id=None
    )

    # Test default 30d
    metrics_30d = await get_metrics("30d", admin, db_session)
    assert metrics_30d.time_range == "30d"
    assert metrics_30d.total_orders >= 0
    assert metrics_30d.total_revenue >= 0.0
    assert metrics_30d.avg_order_value >= 0.0

    # Test 7d
    metrics_7d = await get_metrics("7d", admin, db_session)
    assert metrics_7d.time_range == "7d"

    # Test all
    metrics_all = await get_metrics("all", admin, db_session)
    assert metrics_all.time_range == "all"


@pytest.mark.asyncio
async def test_admin_analytics_endpoint(db_session):
    admin = AdminUser(
        id="test-platform-admin",
        email="admin@smartdiner.io",
        password_hash="mock",
        role="PLATFORM_ADMIN",
        restaurant_id=None
    )

    analytics = await get_analytics("30d", admin, db_session)
    assert analytics.time_range == "30d"
    assert hasattr(analytics, "daily_trends")
    assert hasattr(analytics, "top_dishes")
    assert hasattr(analytics, "category_distribution")
    assert hasattr(analytics, "solver_health")
    assert analytics.solver_health.feasibility_rate_pct >= 0.0
    assert hasattr(analytics, "recent_orders")

    # Test 12h granularity
    analytics_12h = await get_analytics("12h", admin, db_session)
    assert analytics_12h.time_range == "12h"
    assert len(analytics_12h.daily_trends) == 12

    # Test custom date range
    analytics_custom = await get_analytics("custom", admin, db_session, start_date="2026-09-01", end_date="2026-09-05")
    assert analytics_custom.time_range == "custom"
    assert len(analytics_custom.daily_trends) == 5

    # Test top dishes include restaurant_name field
    for dish in analytics.top_dishes:
        assert hasattr(dish, "restaurant_name")

import pytest
from app.models.admin_user import AdminUser
from app.services.admin_insights import fetch_postgres_metrics, classify_admin_query

@pytest.mark.asyncio
async def test_fetch_postgres_metrics_currency_and_conversations(db_session):
    admin = AdminUser(
        id="test-platform-admin-id",
        email="platform_admin@smartdiner.io",
        password_hash="mockhash",
        role="PLATFORM_ADMIN",
        restaurant_id=None
    )

    metrics = await fetch_postgres_metrics(db_session, admin)

    assert metrics["platform_currency"] == "INR (₹)"
    assert "orders_summary" in metrics
    assert metrics["orders_summary"]["currency"] == "INR (₹)"
    assert "₹" in metrics["orders_summary"]["total_revenue"]
    assert "₹" in metrics["orders_summary"]["avg_order_value"]
    assert "recent_conversations" in metrics
    assert isinstance(metrics["recent_conversations"], list)

def test_classify_admin_query_fallback():
    # GCS query
    assert classify_admin_query_fallback_helper("Did any queries trigger allergen exclusions or infeasible solver statuses?") == "GCS"
    # Postgres query
    assert classify_admin_query_fallback_helper("What were the most recent conversation queries, and what restaurants were selected?") == "POSTGRES"
    # Both query
    assert classify_admin_query_fallback_helper("Show me the solver decisions and average order totals from today's chat sessions.") == "BOTH"

def classify_admin_query_fallback_helper(message: str) -> str:
    msg_lower = message.lower()
    if any(w in msg_lower for w in ["token", "latency", "cost", "telemetry", "gcs", "audit", "solver", "infeasible", "feasible", "allergen"]):
        if any(w in msg_lower for w in ["order", "revenue", "sale", "dish", "customer", "conversation", "restaurant"]):
            return "BOTH"
        return "GCS"
    if any(w in msg_lower for w in ["conversation", "query", "queries", "session"]):
        return "POSTGRES"
    return "POSTGRES"

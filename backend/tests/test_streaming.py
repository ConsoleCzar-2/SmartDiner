import pytest
import json
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from app.models.admin_user import AdminUser
from app.models.user import User
from app.models.menu_item import MenuItem
from app.schemas.constraints import ExtractedConstraints
from app.schemas.recommendation import ChatRequest
from app.services.explanation_generator import stream_explanation, generate_explanation
from app.services.recommendation_pipeline import stream_chat_pipeline, process_chat_request
from app.services.admin_insights import stream_admin_insight


@pytest.mark.asyncio
async def test_stream_explanation():
    mock_item = MenuItem(
        id="test-item-1",
        restaurant_id="rest-1",
        name="Paneer Tikka",
        price=320.0,
        category="Starters",
        dietary_preference="Vegetarian",
        spice_level="Medium",
        serving_size=2
    )

    solver_output = {
        "status": "Optimal",
        "total_cost": 320.0,
        "total_servings": 2,
        "items": [
            {
                "item": mock_item,
                "quantity": 1,
                "subtotal": 320.0
            }
        ],
        "decision_rationale": {}
    }
    constraints = ExtractedConstraints(
        people_count=2,
        vegetarian_count=2,
        vegan_count=0,
        non_vegetarian_count=0,
        max_budget=500
    )

    events = []
    async for event in stream_explanation(solver_output, constraints):
        events.append(event)

    assert len(events) >= 2
    token_events = [e for e in events if e["type"] == "token"]
    done_events = [e for e in events if e["type"] == "done"]

    assert len(token_events) > 0
    assert len(done_events) == 1
    assert "telemetry" in done_events[0]
    assert done_events[0]["telemetry"]["step"] == "explanation_generator"
    assert len(done_events[0]["full_text"]) > 0

    # Also test unary adapter
    unary_text, unary_telemetry = await generate_explanation(solver_output, constraints)
    assert len(unary_text) > 0
    assert unary_telemetry["step"] == "explanation_generator"


@pytest.mark.asyncio
async def test_stream_chat_pipeline(db_session):
    unique_suffix = uuid.uuid4().hex[:8]
    user = User(
        id=f"test-stream-user-{unique_suffix}",
        email=f"streamer_{unique_suffix}@smartdiner.io",
        name="Stream User"
    )
    db_session.add(user)
    await db_session.commit()

    request = ChatRequest(
        message="Hello! I need a vegetarian dinner for 2 under 1500.",
        restaurant_id=None,
        conversation_id=None
    )

    frames = []
    async for frame in stream_chat_pipeline(request, db_session, user.id):
        frames.append(frame)

    assert len(frames) > 0
    raw_stream = "".join(frames)
    assert "event: status" in raw_stream
    assert "event: done" in raw_stream

    # Also test unary process_chat_request adapter
    unary_res, unary_telemetry = await process_chat_request(request, db_session, user.id)
    assert unary_res.conversation_id is not None
    assert unary_res.recommendation is not None
    assert "intent" in unary_telemetry


@pytest.mark.asyncio
async def test_stream_admin_insight(db_session):
    admin = AdminUser(
        id="test-stream-admin",
        email="admin_stream@smartdiner.io",
        password_hash="mock",
        role="PLATFORM_ADMIN",
        restaurant_id=None
    )

    frames = []
    async for frame in stream_admin_insight(db_session, admin, "How are our sales performing this month?"):
        frames.append(frame)

    assert len(frames) > 0
    raw_stream = "".join(frames)
    assert "event: status" in raw_stream
    assert "event: metadata" in raw_stream
    assert "event: done" in raw_stream

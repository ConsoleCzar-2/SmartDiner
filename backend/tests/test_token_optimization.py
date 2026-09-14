import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from app.models.user import User
from app.models.restaurant import Restaurant
from app.schemas.constraints import ExtractedConstraints
from app.schemas.recommendation import ChatRequest
from app.services.constraint_extractor import (
    _project_lean_cart, _compact_constraints, _format_compact_history
)
from app.services.explanation_generator import _project_qa_cart, build_question_answer_prompt
from app.services.recommendation_pipeline import process_chat_request


def test_project_lean_cart_strips_heavy_fields():
    raw_cart = [
        {
            "id": "01a09bf8-1791-7401-b30b-79e394bd3090",
            "name": "Butter Chicken Deluxe",
            "category": "Main Course",
            "quantity": 2,
            "unit_price": 450.0,
            "subtotal": 900.0,
            "dietary_preference": "Non-Vegetarian",
            "spice_level": "Medium",
            "serving_size": 2,
            "total_servings": 4,
            "image_url": "https://storage.googleapis.com/smartdiner-assets/butter_chicken_deluxe_hd_image.png"
        },
        {
            "id": "01a09bf8-1791-7401-b30b-79e394bd3091",
            "name": "Garlic Naan",
            "category": "Bread",
            "quantity": 3,
            "unit_price": 60.0,
            "subtotal": 180.0,
            "dietary_preference": "Vegetarian",
            "spice_level": "Low",
            "serving_size": 1,
            "total_servings": 3,
            "image_url": "https://storage.googleapis.com/smartdiner-assets/garlic_naan_hd_image.png"
        }
    ]

    lean = _project_lean_cart(raw_cart)
    assert len(lean) == 2

    item1 = lean[0]
    assert item1["name"] == "Butter Chicken Deluxe"
    assert item1["quantity"] == 2
    assert item1["category"] == "Main Course"
    assert item1["spice_level"] == "Medium"
    assert item1["dietary_preference"] == "Non-Vegetarian"
    assert "id" not in item1
    assert "image_url" not in item1
    assert "unit_price" not in item1
    assert "subtotal" not in item1
    assert "serving_size" not in item1
    assert "total_servings" not in item1


def test_compact_constraints_filters_empty_and_null():
    raw_constraints = {
        "people_count": 2,
        "vegetarian_count": 0,
        "vegan_count": 0,
        "non_vegetarian_count": 2,
        "max_budget": 2000.0,
        "max_spice_level": "Any",
        "excluded_allergens": [],
        "preferred_cuisines": [],
        "preferred_categories": ["Main Course"],
        "category_min_counts": {},
        "specific_dish_requests": [],
        "dish_quantities": {},
        "excluded_dishes": [],
        "is_modification": False
    }

    compact = _compact_constraints(raw_constraints)
    assert "people_count" in compact
    assert "non_vegetarian_count" in compact
    assert "max_budget" in compact
    assert "preferred_categories" in compact
    assert compact["preferred_categories"] == ["Main Course"]

    # Assert empty collections and defaults are pruned
    assert "excluded_allergens" not in compact
    assert "preferred_cuisines" not in compact
    assert "category_min_counts" not in compact
    assert "dish_quantities" not in compact
    assert "excluded_dishes" not in compact
    assert "max_spice_level" not in compact  # 'Any' is default and pruned


def test_format_compact_history_condenses_assistant_narratives():
    history = [
        {"role": "user", "content": "Food for 2 under 2000"},
        {
            "role": "assistant", 
            "content": "I have selected Butter Chicken and Garlic Naan for your meal. The total is ₹1,140 which fits well within your ₹2,000 budget. Let me know if you would like dessert."
        },
        {"role": "user", "content": "Does the butter chicken have nuts?"},
        {
            "role": "assistant",
            "content": "No, our Butter Chicken is prepared with dairy and tomato gravy without tree nuts. It is 100% nut safe."
        }
    ]

    compact_text = _format_compact_history(history, max_turns=2)
    assert "User: Food for 2 under 2000" in compact_text
    assert "User: Does the butter chicken have nuts?" in compact_text
    # Verify assistant responses are condensed to first sentence
    assert "I have selected Butter Chicken and Garlic Naan for your meal." in compact_text
    assert "Let me know if you would like dessert" not in compact_text


def test_project_qa_cart_preserves_facts_without_urls():
    raw_cart = [
        {
            "id": "uuid-123",
            "name": "Chicken Biryani",
            "category": "Main Course",
            "quantity": 1,
            "unit_price": 380.0,
            "dietary_preference": "Non-Vegetarian",
            "spice_level": "Medium",
            "serving_size": 2,
            "image_url": "https://storage.googleapis.com/smartdiner-assets/biryani.png"
        }
    ]
    qa = _project_qa_cart(raw_cart)
    assert len(qa) == 1
    item = qa[0]
    assert item["name"] == "Chicken Biryani"
    assert item["quantity"] == 1
    assert item["unit_price"] == "₹380.0"
    assert item["spice_level"] == "Medium"
    assert item["serving_size"] == 2
    assert "image_url" not in item
    assert "id" not in item


@pytest.mark.asyncio
@patch("app.services.recommendation_pipeline.classify_intent")
@patch("app.services.recommendation_pipeline.extract_constraints")
@patch("app.services.recommendation_pipeline.stream_question_answer")
async def test_question_intent_bypasses_constraint_extractor(
    mock_stream_qa, mock_extract, mock_classify, db_session
):
    """Verifies that QUESTION intent routes directly to QA and never calls extract_constraints."""
    unique_suffix = uuid.uuid4().hex[:8]
    user = User(
        id=f"test-qa-user-{unique_suffix}",
        email=f"qa_{unique_suffix}@smartdiner.io",
        name="QA User"
    )
    db_session.add(user)
    await db_session.commit()

    # Mock classify_intent returning QUESTION
    mock_intent_res = MagicMock()
    mock_intent_res.intent = "QUESTION"
    mock_intent_res.reason = "User asking about allergens"
    mock_intent_res.model_dump.return_value = {"intent": "QUESTION", "reason": "User asking about allergens"}
    mock_classify.return_value = (mock_intent_res, {"step": "intent_classifier", "prompt_tokens": 400, "total_tokens": 420})

    # Mock stream_question_answer
    async def fake_qa_stream(*args, **kwargs):
        yield {"type": "token", "content": "Our butter chicken does not contain nuts."}
        yield {"type": "done", "full_text": "Our butter chicken does not contain nuts.", "telemetry": {"step": "explanation_generator", "prompt_tokens": 700, "total_tokens": 750}}
    mock_stream_qa.side_effect = fake_qa_stream

    req = ChatRequest(message="Does the butter chicken contain nuts?")
    response, telemetry = await process_chat_request(req, db_session, user.id)

    # CRITICAL ASSERTION: extract_constraints was bypassed completely
    mock_extract.assert_not_called()
    assert response.explanation == "Our butter chicken does not contain nuts."
    # Telemetry should only have intent_classifier and explanation_generator, NOT constraint_extractor
    steps = [call.get("step") for call in telemetry["llm_calls"]]
    assert "constraint_extractor" not in steps
    assert "intent_classifier" in steps


@pytest.mark.asyncio
@patch("app.services.recommendation_pipeline.classify_intent")
@patch("app.services.recommendation_pipeline.extract_constraints")
async def test_greeting_intent_bypasses_constraint_extractor(
    mock_extract, mock_classify, db_session
):
    """Verifies that GREETING intent immediately returns welcome response without extract_constraints."""
    unique_suffix = uuid.uuid4().hex[:8]
    user = User(
        id=f"test-greet-user-{unique_suffix}",
        email=f"greet_{unique_suffix}@smartdiner.io",
        name="Greet User"
    )
    db_session.add(user)
    await db_session.commit()

    mock_intent_res = MagicMock()
    mock_intent_res.intent = "GREETING"
    mock_intent_res.reason = "Hello greeting"
    mock_intent_res.model_dump.return_value = {"intent": "GREETING", "reason": "Hello greeting"}
    mock_classify.return_value = (mock_intent_res, {"step": "intent_classifier", "prompt_tokens": 350, "total_tokens": 370})

    req = ChatRequest(message="Hello there!")
    response, telemetry = await process_chat_request(req, db_session, user.id)

    mock_extract.assert_not_called()
    assert "Hello! Welcome to SmartDiner" in response.explanation
    steps = [call.get("step") for call in telemetry["llm_calls"]]
    assert "constraint_extractor" not in steps
    assert steps == ["intent_classifier"]

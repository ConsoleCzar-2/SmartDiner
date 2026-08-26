import pytest
from unittest.mock import AsyncMock, patch
from app.schemas.constraints import ExtractedConstraints
from app.services.constraint_extractor import extract_constraints

pytestmark = pytest.mark.asyncio

# A helper to create a mock response matching what google-genai returns
def create_mock_response(json_data: str):
    class MockResponse:
        text = json_data
    return MockResponse()

@patch('app.services.constraint_extractor.genai.Client')
async def test_extract_basic_order(mock_client_class):
    mock_instance = mock_client_class.return_value
    mock_instance.aio.models.generate_content = AsyncMock(return_value=create_mock_response(
        '{"people_count": 3, "vegetarian_count": 1, "non_vegetarian_count": null, "max_budget": 1500.0, "max_spice_level": "High", "excluded_allergens": [], "preferred_cuisines": [], "preferred_categories": [], "specific_dish_requests": [], "is_modification": false}'
    ))
    
    msg = "We are 3 friends, one of us is vegetarian. Make it spicy. Budget is around 1500 INR."
    result = await extract_constraints(msg)
    
    assert result.people_count == 3
    assert result.vegetarian_count == 1
    assert result.max_budget == 1500.0
    assert result.max_spice_level in ["High", "Extreme"]
    assert result.is_modification is False

@patch('app.services.constraint_extractor.genai.Client')
async def test_extract_allergy_mapping(mock_client_class):
    mock_instance = mock_client_class.return_value
    mock_instance.aio.models.generate_content = AsyncMock(return_value=create_mock_response(
        '{"people_count": 1, "vegetarian_count": 0, "non_vegetarian_count": null, "max_budget": null, "max_spice_level": "Any", "excluded_allergens": ["Dairy", "Gluten"], "preferred_cuisines": [], "preferred_categories": [], "specific_dish_requests": [], "is_modification": false}'
    ))
    
    msg = "I am allergic to cheese and wheat. Just 1 person."
    result = await extract_constraints(msg)
    
    assert result.people_count == 1
    assert "Dairy" in result.excluded_allergens
    assert "Gluten" in result.excluded_allergens

@patch('app.services.constraint_extractor.genai.Client')
async def test_extract_modification(mock_client_class):
    mock_instance = mock_client_class.return_value
    mock_instance.aio.models.generate_content = AsyncMock(return_value=create_mock_response(
        '{"people_count": 4, "vegetarian_count": 0, "non_vegetarian_count": null, "max_budget": 2000.0, "max_spice_level": "Any", "excluded_allergens": [], "preferred_cuisines": [], "preferred_categories": [], "specific_dish_requests": [], "is_modification": true}'
    ))
    
    msg = "Actually, let's make it for 4 people and increase the budget to 2000."
    history = [{"role": "user", "content": "I need dinner for 3, budget 1500"}]
    result = await extract_constraints(msg, conversation_history=history)
    
    assert result.people_count == 4
    assert result.max_budget == 2000.0
    assert result.is_modification is True

@patch('app.services.constraint_extractor.genai.Client')
async def test_extract_cheap_no_budget(mock_client_class):
    mock_instance = mock_client_class.return_value
    mock_instance.aio.models.generate_content = AsyncMock(return_value=create_mock_response(
        '{"people_count": 2, "vegetarian_count": 0, "non_vegetarian_count": null, "max_budget": null, "max_spice_level": "Any", "excluded_allergens": [], "preferred_cuisines": [], "preferred_categories": [], "specific_dish_requests": [], "is_modification": false}'
    ))
    
    msg = "We want a cheap meal for 2 people."
    result = await extract_constraints(msg)
    
    assert result.people_count == 2
    assert result.max_budget is None

@patch('app.services.constraint_extractor.genai.Client')
async def test_extract_specific_dish(mock_client_class):
    mock_instance = mock_client_class.return_value
    mock_instance.aio.models.generate_content = AsyncMock(return_value=create_mock_response(
        '{"people_count": 2, "vegetarian_count": 0, "non_vegetarian_count": null, "max_budget": null, "max_spice_level": "Any", "excluded_allergens": [], "preferred_cuisines": [], "preferred_categories": [], "specific_dish_requests": ["butter chicken", "garlic naan"], "is_modification": false}'
    ))
    
    msg = "Get me some butter chicken and garlic naan for 2 people."
    result = await extract_constraints(msg)
    
    assert result.people_count == 2
    dishes = [d.lower() for d in result.specific_dish_requests]
    assert any("butter chicken" in d for d in dishes)
    assert any("naan" in d for d in dishes)

@patch('app.services.constraint_extractor.genai.Client')
async def test_extract_slang_allergies(mock_client_class):
    mock_instance = mock_client_class.return_value
    mock_instance.aio.models.generate_content = AsyncMock(return_value=create_mock_response(
        '{"people_count": 1, "vegetarian_count": 0, "non_vegetarian_count": null, "max_budget": null, "max_spice_level": "Any", "excluded_allergens": ["Peanuts"], "preferred_cuisines": [], "preferred_categories": [], "specific_dish_requests": [], "is_modification": false}'
    ))
    
    msg = "Can't have peanuts bro, will literally die. Table for 1."
    result = await extract_constraints(msg)
    
    assert result.people_count == 1
    assert "Peanuts" in result.excluded_allergens

@patch('app.services.constraint_extractor.genai.Client')
async def test_extract_cuisine_preference(mock_client_class):
    mock_instance = mock_client_class.return_value
    mock_instance.aio.models.generate_content = AsyncMock(return_value=create_mock_response(
        '{"people_count": 2, "vegetarian_count": 0, "non_vegetarian_count": null, "max_budget": null, "max_spice_level": "Any", "excluded_allergens": [], "preferred_cuisines": ["Chinese"], "preferred_categories": [], "specific_dish_requests": [], "is_modification": false}'
    ))
    
    msg = "I'm feeling like Chinese tonight. 2 people."
    result = await extract_constraints(msg)
    
    assert result.people_count == 2
    assert any("Chinese" in c for c in result.preferred_cuisines)

@patch('app.services.constraint_extractor.genai.Client')
async def test_extract_contradictory_input(mock_client_class):
    mock_instance = mock_client_class.return_value
    mock_instance.aio.models.generate_content = AsyncMock(return_value=create_mock_response(
        '{"people_count": 3, "vegetarian_count": 0, "non_vegetarian_count": null, "max_budget": null, "max_spice_level": "Any", "excluded_allergens": [], "preferred_cuisines": [], "preferred_categories": [], "specific_dish_requests": [], "is_modification": false}'
    ))
    
    msg = "We are 2 people, wait no 3 people."
    result = await extract_constraints(msg)
    
    assert result.people_count == 3

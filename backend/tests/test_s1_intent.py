import json
import pytest
from unittest.mock import AsyncMock, patch

from backend.llm.client import GeminiClient
from backend.llm.errors import LLMValidationError
from backend.stages.s1_intent.extractor import IntentExtractor
from backend.schemas import StructuredIntent

@pytest.fixture
def mock_llm_client():
    client = AsyncMock(spec=GeminiClient)
    return client

@pytest.mark.asyncio
async def test_extractor_success(mock_llm_client):
    # Setup the mock to return a valid StructuredIntent
    mock_intent = StructuredIntent.model_validate({
        "app_name": "TestApp",
        "app_type": "web_application",
        "description": "A test application",
        "target_users": ["admin"],
        "core_features": [
            {"name": "login", "description": "User login", "priority": "high"}
        ],
        "constraints": {"auth_required": True, "realtime": False, "file_uploads": False, "multi_tenancy": False, "i18n": False}
    })
    mock_llm_client.generate_structured.return_value = mock_intent

    extractor = IntentExtractor(mock_llm_client)
    result = await extractor.execute("Build a test app with admin login.")

    # Verify the client was called with the right prompt and schema
    mock_llm_client.generate_structured.assert_called_once()
    kwargs = mock_llm_client.generate_structured.call_args.kwargs
    assert "Build a test app with admin login." in kwargs["prompt"]
    assert kwargs["response_model"] == StructuredIntent
    
    # Verify result
    assert result == mock_intent
    assert result.app_name == "TestApp"


@pytest.mark.asyncio
async def test_extractor_llm_validation_error(mock_llm_client):
    # Setup the mock to raise a validation error (simulating bad JSON from LLM)
    mock_llm_client.generate_structured.side_effect = LLMValidationError("Invalid JSON")

    extractor = IntentExtractor(mock_llm_client)
    
    with pytest.raises(LLMValidationError):
        await extractor.execute("Build something broken.")

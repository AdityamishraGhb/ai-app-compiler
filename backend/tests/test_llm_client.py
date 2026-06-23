import json
import pytest
from unittest.mock import AsyncMock, patch

from backend.llm.client import GeminiClient
from backend.llm.errors import LLMValidationError, LLMRateLimitError
from backend.schemas import StructuredIntent
from google.api_core.exceptions import ResourceExhausted

@pytest.fixture
def gemini_client():
    with patch("backend.llm.client.genai.GenerativeModel") as mock_model:
        client = GeminiClient(api_key="fake-key")
        client.model = AsyncMock()
        return client

@pytest.mark.asyncio
async def test_generate_structured_success(gemini_client):
    # Mock valid JSON response
    valid_json = """
    ```json
        {
            "app_name": "TestApp",
            "app_type": "web_application",
            "description": "A valid description for testing",
            "target_users": ["user"],
            "core_features": [{"name": "feat", "description": "desc", "priority": "high"}],
            "constraints": {}
        }  ```
    """
    mock_response = AsyncMock()
    mock_response.text = valid_json
    gemini_client.model.generate_content_async.return_value = mock_response

    result = await gemini_client.generate_structured("Prompt", StructuredIntent)
    
    assert isinstance(result, StructuredIntent)
    assert result.app_name == "TestApp"

@pytest.mark.asyncio
async def test_generate_structured_invalid_json(gemini_client):
    # Mock invalid JSON response
    mock_response = AsyncMock()
    mock_response.text = "This is not JSON"
    gemini_client.model.generate_content_async.return_value = mock_response

    with pytest.raises(LLMValidationError, match="LLM did not return valid JSON"):
        await gemini_client.generate_structured("Prompt", StructuredIntent)

@pytest.mark.asyncio
async def test_generate_structured_validation_error(gemini_client):
    # Mock valid JSON but missing required fields
    invalid_schema_json = '{"app_name": "TestApp"}'
    mock_response = AsyncMock()
    mock_response.text = invalid_schema_json
    gemini_client.model.generate_content_async.return_value = mock_response

    with pytest.raises(LLMValidationError, match="Failed to validate LLM output"):
        await gemini_client.generate_structured("Prompt", StructuredIntent)

@pytest.mark.asyncio
async def test_async_retry_rate_limit(gemini_client):
    # Mock ResourceExhausted exception
    gemini_client.model.generate_content_async.side_effect = ResourceExhausted("Rate limit")

    with patch("backend.llm.client.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(LLMRateLimitError):
            # Should retry 3 times by default
            await gemini_client.generate_structured("Prompt", StructuredIntent)
        
        assert mock_sleep.call_count == 2 # Sleeps before 2nd and 3rd attempt

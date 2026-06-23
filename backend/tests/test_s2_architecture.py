import pytest
from unittest.mock import AsyncMock

from backend.llm.client import GeminiClient
from backend.stages.s2_architecture.designer import ArchitectureDesigner
from backend.schemas import StructuredIntent, ArchitectureBlueprint

@pytest.fixture
def mock_llm_client():
    client = AsyncMock(spec=GeminiClient)
    return client

@pytest.fixture
def sample_intent():
    return StructuredIntent.model_validate({
        "app_name": "BandManager",
        "app_type": "band_management_system",
        "description": "Band app with more than 10 characters",
        "target_users": ["admin", "member"],
        "core_features": [
            {"name": "manage_songs", "description": "Manage songs", "priority": "high"}
        ],
        "constraints": {}
    })

@pytest.mark.asyncio
async def test_designer_success(mock_llm_client, sample_intent):
    mock_blueprint = ArchitectureBlueprint.model_validate({
        "entities": [
            {
                "name": "Song",
                "description": "A musical track",
                "attributes": [{"name": "title", "type": "string", "primary_key": False, "required": True, "unique": False, "foreign_key": None, "enum_values": None, "description": ""}]
            }
        ],
        "roles": [
            {"name": "admin", "description": "Administrator", "permissions": ["manage_songs"]}
        ],
        "pages": [
            {"name": "Dashboard", "route": "/dashboard", "description": "Main view", "auth_required": True, "allowed_roles": ["admin"]}
        ],
        "features": [
            {"name": "manage_songs", "description": "Manage songs", "entities_involved": ["Song"], "operations": ["create", "read", "update", "delete"]}
        ],
        "flows": [
            {"name": "add_song", "description": "Add a new song", "actor": "admin", "steps": ["Go to dashboard", "Click add song"], "preconditions": [], "postconditions": []}
        ]
    })
    
    mock_llm_client.generate_structured.return_value = mock_blueprint
    
    designer = ArchitectureDesigner(mock_llm_client)
    result = await designer.execute(sample_intent)
    
    mock_llm_client.generate_structured.assert_called_once()
    kwargs = mock_llm_client.generate_structured.call_args.kwargs
    
    assert sample_intent.model_dump_json(indent=2) in kwargs["prompt"]
    assert kwargs["response_model"] == ArchitectureBlueprint
    
    assert result == mock_blueprint
    assert len(result.entities) == 1
    assert result.entities[0].name == "Song"

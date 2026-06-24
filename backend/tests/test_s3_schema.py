import pytest
from unittest.mock import AsyncMock, patch

from backend.llm.client import GeminiClient
from backend.schemas import (
    ArchitectureBlueprint,
    UISchema,
    APISchema,
    DatabaseSchema,
    AuthSchema,
    SchemaBundle,
)
from backend.stages.s3_schema.bundler import SchemaBundler, BundleValidationError

@pytest.fixture
def mock_blueprint():
    return ArchitectureBlueprint.model_validate({
        "entities": [
            {
                "name": "User",
                "description": "User entity",
                "attributes": [{"name": "id", "type": "uuid", "primary_key": True, "required": True, "unique": True, "foreign_key": None, "enum_values": None, "description": ""}]
            }
        ],
        "roles": [
            {"name": "admin", "description": "Admin", "permissions": ["all"]}
        ],
        "pages": [
            {"name": "Dashboard", "route": "/dashboard", "description": "Dashboard", "auth_required": True, "allowed_roles": []}
        ],
        "features": [
            {"name": "manage_users", "description": "User management", "entities_involved": ["User"], "operations": ["create"]}
        ],
        "flows": []
    })

@pytest.fixture
def mock_valid_bundle():
    ui = UISchema.model_validate({
        "pages": [
            {
                "name": "DashboardPage",
                "route": "/dashboard",
                "layout": "sidebar",
                "auth_required": True,
                "allowed_roles": [],
                "components": [
                    {
                        "type": "data_table",
                        "id": "users_table",
                        "data_source": "GET /users",
                        "columns": [],
                        "fields": [],
                        "actions": []
                    }
                ]
            }
        ]
    })
    api = APISchema.model_validate({"endpoints": [
        {
            "method": "GET",
            "path": "/users",
            "description": "Get users",
            "auth_required": True,
            "allowed_roles": ["admin"],
            "request_body": None,
            "response": {"type": "list", "entity": "User", "fields": []}
        }
    ]})
    db = DatabaseSchema.model_validate({"tables": [
        {
            "name": "users",
            "entity": "User",
            "columns": [{"name": "id", "type": "TEXT", "primary_key": True, "nullable": False, "unique": True, "foreign_key": None, "comment": ""}],
            "indexes": []
        }
    ]})
    auth = AuthSchema.model_validate({
        "strategy": "jwt",
        "roles": [{"name": "admin", "permissions": ["all"]}],
        "credentials": {"identifier_field": "email", "secret_field": "password"},
        "route_guards": []
    })
    
    return SchemaBundle(ui=ui, api=api, database=db, auth=auth)

@pytest.mark.asyncio
async def test_bundler_success(mock_blueprint, mock_valid_bundle):
    client = AsyncMock(spec=GeminiClient)
    bundler = SchemaBundler(client)
    
    # Mock the individual generator executions
    bundler.ui_gen.execute = AsyncMock(return_value=mock_valid_bundle.ui)
    bundler.api_gen.execute = AsyncMock(return_value=mock_valid_bundle.api)
    bundler.db_gen.execute = AsyncMock(return_value=mock_valid_bundle.database)
    bundler.auth_gen.execute = AsyncMock(return_value=mock_valid_bundle.auth)
    
    result = await bundler.execute(mock_blueprint)
    
    assert result == mock_valid_bundle
    bundler.ui_gen.execute.assert_called_once()
    bundler.api_gen.execute.assert_called_once()
    bundler.db_gen.execute.assert_called_once()
    bundler.auth_gen.execute.assert_called_once()

@pytest.mark.asyncio
async def test_bundler_validation_failure(mock_blueprint, mock_valid_bundle):
    # Introduce referential error: API entity does not exist in DB
    invalid_bundle = mock_valid_bundle.model_copy(deep=True)
    invalid_bundle.api.endpoints[0].response.entity = "NonExistentTable"
    
    client = AsyncMock(spec=GeminiClient)
    bundler = SchemaBundler(client)
    
    bundler.ui_gen.execute = AsyncMock(return_value=invalid_bundle.ui)
    bundler.api_gen.execute = AsyncMock(return_value=invalid_bundle.api)
    bundler.db_gen.execute = AsyncMock(return_value=invalid_bundle.database)
    bundler.auth_gen.execute = AsyncMock(return_value=invalid_bundle.auth)
    
    with pytest.raises(BundleValidationError) as exc_info:
        await bundler.execute(mock_blueprint)
        
    assert len(exc_info.value.issues) == 1
    issue = exc_info.value.issues[0]
    assert issue.category == "referential"
    assert issue.severity == "error"
    assert "NonExistentTable" in issue.message

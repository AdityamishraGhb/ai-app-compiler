import pytest

from backend.schemas import (
    ArchitectureBlueprint,
    Entity,
    EntityAttribute,
    AuthRole,
    RoleDefinition,
    PageDefinition,
    FeatureDefinition,
    SchemaBundle,
    UISchema,
    APISchema,
    DatabaseSchema,
    AuthSchema,
    ValidationSeverity,
    ValidationCategory,
)
from backend.stages.s4_validation.engine import ValidationEngine

@pytest.fixture
def mock_blueprint():
    return ArchitectureBlueprint(
        entities=[
            Entity(name="User", description="User entity", attributes=[EntityAttribute(name="id", type="string"), EntityAttribute(name="email", type="string")])
        ],
        roles=[RoleDefinition(name="admin", permissions=["all"])],
        pages=[PageDefinition(name="Dashboard", route="/dashboard", description="Main dashboard")],
        features=[FeatureDefinition(name="core_feature", description="Basic feature", entities_involved=["User"], operations=["create"])],
        flows=[]
    )

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
            "columns": [
                {"name": "id", "type": "TEXT", "primary_key": True, "nullable": False, "unique": True, "foreign_key": None, "comment": ""},
                {"name": "email", "type": "TEXT", "primary_key": False, "nullable": False, "unique": True, "foreign_key": None, "comment": ""},
                {"name": "password", "type": "TEXT", "primary_key": False, "nullable": False, "unique": False, "foreign_key": None, "comment": ""}
            ],
            "indexes": []
        }
    ]})
    auth = AuthSchema.model_validate({
        "strategy": "jwt",
        "roles": [{"name": "admin", "permissions": ["all"]}],
        "user_entity": "User",
        "credentials": {"identifier_field": "email", "secret_field": "password"},
        "route_guards": []
    })
    
    return SchemaBundle(ui=ui, api=api, database=db, auth=auth)

def test_validation_engine_success(mock_valid_bundle, mock_blueprint):
    engine = ValidationEngine()
    report = engine.execute(mock_valid_bundle, mock_blueprint)
    
    assert report.is_valid is True
    assert report.total_issues == 0
    assert len(report.issues) == 0

def test_validation_engine_failure_collection(mock_valid_bundle, mock_blueprint):
    # Introduce multiple distinct referential and logical errors
    invalid_bundle = mock_valid_bundle.model_copy(deep=True)
    
    # 1. Database: foreign key to non-existent table
    from backend.schemas import DBColumn, ForeignKeyRef
    invalid_bundle.database.tables[0].columns.append(
        DBColumn(name="team_id", type="TEXT", primary_key=False, nullable=True, unique=False, foreign_key=ForeignKeyRef(table="teams", column="id"), comment="")
    )
    
    # 2. API to DB: endpoint entity does not exist
    invalid_bundle.api.endpoints[0].response.entity = "UnknownEntity"
    
    # 3. UI to API: non-existent endpoint
    invalid_bundle.ui.pages[0].components[0].data_source = "POST /nothing"
    
    # 4. Auth: role does not exist in blueprint
    invalid_bundle.auth.roles.append(AuthRole(name="superadmin", permissions=["read"]))
    
    # 5. Auth credentials map to non-existent columns
    invalid_bundle.auth.credentials.identifier_field = "username_missing"
    
    engine = ValidationEngine()
    report = engine.execute(invalid_bundle, mock_blueprint)
    
    assert report.is_valid is False
    assert report.total_issues == 5
    assert report.error_count == 5
    
    # Verify categories and messages
    issue_targets = {i.target for i in report.issues}
    assert "DBTable[teams]" in issue_targets
    assert "DBTable[entity=UnknownEntity]" in issue_targets
    assert "APIEndpoint[POST /nothing]" in issue_targets
    assert "ArchitectureBlueprint.roles" in issue_targets
    assert "DBTable[users].columns[username_missing]" in issue_targets

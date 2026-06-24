import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.llm.client import GeminiClient
from backend.stages.s5_repair.engine import RepairEngine
from backend.schemas import (
    ArchitectureBlueprint,
    StructuredIntent,
    SchemaBundle,
    ValidationReport,
    ValidationIssue,
    ValidationSeverity,
    ValidationCategory,
    DatabaseSchema,
    APISchema,
    UISchema,
    AuthSchema,
    DBTable,
    DBColumn,
    ForeignKeyRef,
    Entity,
    EntityAttribute,
    RoleDefinition,
    PageDefinition,
    FeatureDefinition,
    CoreFeature,
)

@pytest.fixture
def mock_llm_client():
    client = MagicMock(spec=GeminiClient)
    client.generate_structured = AsyncMock()
    return client

@pytest.fixture
def mock_blueprint():
    # Provide a simple blueprint
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
def mock_intent():
    return StructuredIntent(
        app_name="TestApp",
        description="A test app",
        app_type="CRUD",
        core_features=[CoreFeature(name="Create user", description="Create users", priority="high")],
        target_users=["admins"]
    )

@pytest.mark.asyncio
async def test_repair_engine_success(mock_llm_client, mock_blueprint, mock_intent):
    # Setup bundle
    bundle = SchemaBundle(
        ui=UISchema.model_validate({
            "pages": [{"name": "P1", "route": "/p", "layout": "sidebar", "auth_required": False, "allowed_roles": [], "components": [{"type": "data_table", "id": "t1", "data_source": None, "columns": [], "fields": [], "actions": []}]}]
        }),
        api=APISchema.model_validate({
            "endpoints": [{"method": "GET", "path": "/p", "description": "D", "auth_required": False, "allowed_roles": [], "request_body": None, "response": {"type": "single", "entity": "E", "fields": []}}]
        }),
        database=DatabaseSchema.model_validate({
            "tables": [{
                "name": "users", "entity": "User", "columns": [
                    {"name": "team_id", "type": "TEXT", "primary_key": False, "nullable": True, "unique": False, "foreign_key": {"table": "teams", "column": "id"}, "comment": ""}
                ], "indexes": []
            }]
        }),
        auth=AuthSchema.model_validate({
            "strategy": "jwt", "roles": [{"name": "admin", "permissions": ["all"]}], "user_entity": "User", "credentials": {"identifier_field": "email", "secret_field": "password"}, "route_guards": []
        })
    )
    
    # Setup initial validation report with 1 DB issue
    initial_report = ValidationReport(
        is_valid=False,
        total_issues=1,
        error_count=1,
        warning_count=0,
        info_count=0,
        issues=[
            ValidationIssue(
                id="val-1",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.REFERENTIAL,
                source="DBTable[users].column[team_id].foreign_key",
                target="DBTable[teams]",
                message="Foreign key 'teams.id' references non-existent table 'teams'.",
                repair_hint="Fix it."
            )
        ]
    )

    # We mock the validation engine used inside RepairEngine to return a CLEAN report after repair
    clean_report = ValidationReport(is_valid=True, total_issues=0, error_count=0, warning_count=0, info_count=0, issues=[])

    engine = RepairEngine(llm_client=mock_llm_client)
    # mock the internal validation engine's execute method
    engine.validation_engine.execute = MagicMock(return_value=clean_report)
    
    # Mock LLM to return a fixed DB schema
    repaired_db = bundle.database.model_copy(deep=True)
    repaired_db.tables[0].columns[0].foreign_key = None # Fixed
    mock_llm_client.generate_structured.return_value = repaired_db

    repaired_bundle, final_report, repair_report = await engine.execute(
        bundle=bundle,
        report=initial_report,
        blueprint=mock_blueprint,
        intent=mock_intent
    )

    # Verify LLM was called exactly once for DatabaseSchema
    mock_llm_client.generate_structured.assert_called_once()
    kwargs = mock_llm_client.generate_structured.call_args.kwargs
    assert kwargs["response_model"] == DatabaseSchema

    # Verify repair report
    assert repair_report.issues_received == 1
    assert repair_report.issues_fixed == 1
    assert repair_report.issues_remaining == 0
    assert repair_report.repair_success_rate == 100.0
    
    assert len(repair_report.repair_actions) == 1
    action = repair_report.repair_actions[0]
    assert action.issue_id == "val-1"
    assert action.component_modified == "DatabaseSchema"
    assert action.strategy_used == "LLM_REGENERATION"
    assert action.success is True

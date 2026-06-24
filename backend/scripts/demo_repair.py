import asyncio
import json
import logging
import os
from unittest.mock import AsyncMock

from backend.llm.client import GeminiClient
from backend.schemas import (
    ArchitectureBlueprint,
    StructuredIntent,
    SchemaBundle,
    UISchema,
    APISchema,
    DatabaseSchema,
    AuthSchema,
    ValidationReport,
    Entity,
    EntityAttribute,
    RoleDefinition,
    PageDefinition,
    FeatureDefinition,
    CoreFeature,
)
from backend.stages.s4_validation.engine import ValidationEngine
from backend.stages.s5_repair.engine import RepairEngine

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

async def run_demo():
    print("=" * 60)
    print("REPAIR ENGINE - LIVE DEMO")
    print("=" * 60)

    # 1. Mock inputs
    blueprint = ArchitectureBlueprint(
        entities=[
            Entity(name="User", description="User entity", attributes=[EntityAttribute(name="id", type="string"), EntityAttribute(name="email", type="string")])
        ],
        roles=[RoleDefinition(name="admin", permissions=["all"])],
        pages=[PageDefinition(name="Dashboard", route="/dashboard", description="Main dashboard")],
        features=[FeatureDefinition(name="core_feature", description="Basic feature", entities_involved=["User"], operations=["create"])],
        flows=[]
    )
    
    intent = StructuredIntent(
        app_name="DemoApp",
        description="Demo App for testing repair engine",
        app_type="CRUD",
        core_features=[CoreFeature(name="Create user", description="Creates user", priority="high")],
        target_users=["admins"]
    )

    # 2. Intentionally broken SchemaBundle
    bundle = SchemaBundle(
        ui=UISchema.model_validate({
            "pages": [{"name": "P1", "route": "/p", "layout": "sidebar", "auth_required": False, "allowed_roles": [], "components": [{"type": "data_table", "id": "t1", "data_source": "GET /nothing", "columns": [], "fields": [], "actions": []}]}]
        }),
        api=APISchema.model_validate({
            "endpoints": [{"method": "GET", "path": "/p", "description": "D", "auth_required": False, "allowed_roles": [], "request_body": None, "response": {"type": "single", "entity": "UnknownEntity", "fields": []}}]
        }),
        database=DatabaseSchema.model_validate({
            "tables": [{
                "name": "users", "entity": "User", "columns": [
                    {"name": "team_id", "type": "TEXT", "primary_key": False, "nullable": True, "unique": False, "foreign_key": {"table": "teams", "column": "id"}, "comment": ""}
                ], "indexes": []
            }]
        }),
        auth=AuthSchema.model_validate({
            "strategy": "jwt", "roles": [{"name": "superadmin", "permissions": ["all"]}], "user_entity": "User", "credentials": {"identifier_field": "email", "secret_field": "password"}, "route_guards": []
        })
    )

    # 3. Generate ValidationReport #1
    val_engine = ValidationEngine()
    report1 = val_engine.execute(bundle, blueprint)

    print("\n[ValidationReport #1 - Before Repair]")
    print(f"Total Issues: {report1.total_issues}")
    for i in report1.issues:
        print(f"  - [{i.id}] {i.message}")

    # 4. Setup Gemini Client (or mock if no API key)
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print("\n[Using Real Gemini API for Repair]")
        client = GeminiClient(api_key=api_key)
    else:
        print("\n[No GEMINI_API_KEY found. Using Mock LLM for Repair]")
        # Create a mock that just fixes the known issues deterministically
        client = GeminiClient(api_key="mock")
        client.generate_structured = AsyncMock()
        
        async def mock_generate(prompt, response_model):
            if response_model == DatabaseSchema:
                new_db = bundle.database.model_copy(deep=True)
                new_db.tables[0].columns[0].foreign_key = None # Fix DB
                return new_db
            elif response_model == APISchema:
                new_api = bundle.api.model_copy(deep=True)
                new_api.endpoints[0].response.entity = "User" # Fix API
                return new_api
            elif response_model == UISchema:
                new_ui = bundle.ui.model_copy(deep=True)
                new_ui.pages[0].components[0].data_source = "GET /p" # Fix UI
                return new_ui
            elif response_model == AuthSchema:
                new_auth = bundle.auth.model_copy(deep=True)
                new_auth.roles[0].name = "admin" # Fix Auth
                return new_auth

        client.generate_structured.side_effect = mock_generate

    engine = RepairEngine(llm_client=client)
    
    print("\n[Running Repair Engine...]")
    repaired_bundle, report2, repair_report = await engine.execute(bundle, report1, blueprint, intent)

    print("\n============================================================")
    print("REPAIR SUMMARY")
    print("============================================================")
    print(f"Issues Received: {repair_report.issues_received}")
    print(f"Issues Fixed:    {repair_report.issues_fixed}")
    print(f"Issues Remaining:{repair_report.issues_remaining}")
    print(f"Success Rate:    {repair_report.repair_success_rate}%")
    print("\nActions Taken:")
    for action in repair_report.repair_actions:
        status = "SUCCESS" if action.success else "FAILED"
        print(f"  - Issue {action.issue_id} -> {action.component_modified} [{action.strategy_used}] -> {status}")

    print("\n[ValidationReport #2 - After Repair]")
    print(f"Remaining Issues: {report2.total_issues}")
    for i in report2.issues:
        print(f"  - [{i.id}] {i.message}")

    # Save output to a file
    with open("demo_repair_report.json", "w") as f:
        f.write(repair_report.model_dump_json(indent=2))
    print("\nRepairReport written to demo_repair_report.json")


if __name__ == "__main__":
    asyncio.run(run_demo())

import json
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
    DBColumn,
    ForeignKeyRef,
)
from backend.stages.s4_validation.engine import ValidationEngine

def run_demo():
    print("=" * 60)
    print("VALIDATION ENGINE - LIVE DEMO (0 LLM Calls)")
    print("=" * 60)

    # 1. Create a valid mock architecture
    blueprint = ArchitectureBlueprint(
        entities=[
            Entity(name="User", description="User entity", attributes=[EntityAttribute(name="id", type="string"), EntityAttribute(name="email", type="string")])
        ],
        roles=[RoleDefinition(name="admin", permissions=["all"])],
        pages=[PageDefinition(name="Dashboard", route="/dashboard", description="Main dashboard")],
        features=[FeatureDefinition(name="core_feature", description="Basic feature", entities_involved=["User"], operations=["create"])],
        flows=[]
    )

    # 2. Create an intentionally broken SchemaBundle
    bundle = SchemaBundle(
        ui=UISchema.model_validate({
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
                            "data_source": "GET /nothing", # ERROR 1: Non-existent endpoint
                            "columns": [],
                            "fields": [],
                            "actions": []
                        }
                    ]
                }
            ]
        }),
        api=APISchema.model_validate({"endpoints": [
            {
                "method": "GET",
                "path": "/users",
                "description": "Get users",
                "auth_required": True,
                "allowed_roles": ["admin"],
                "request_body": None,
                "response": {"type": "list", "entity": "UnknownEntity", "fields": []} # ERROR 2: Non-existent entity
            }
        ]}),
        database=DatabaseSchema.model_validate({"tables": [
            {
                "name": "users",
                "entity": "User",
                "columns": [
                    {"name": "id", "type": "TEXT", "primary_key": True, "nullable": False, "unique": True, "foreign_key": None, "comment": ""},
                    {"name": "email", "type": "TEXT", "primary_key": False, "nullable": False, "unique": True, "foreign_key": None, "comment": ""},
                    # ERROR 3: Broken foreign key
                    {"name": "team_id", "type": "TEXT", "primary_key": False, "nullable": True, "unique": False, "foreign_key": {"table": "teams", "column": "id"}, "comment": ""}
                ],
                "indexes": []
            }
        ]}),
        auth=AuthSchema.model_validate({
            "strategy": "jwt",
            "roles": [
                {"name": "admin", "permissions": ["all"]},
                {"name": "superadmin", "permissions": ["read"]} # ERROR 4: Role not in blueprint
            ],
            "user_entity": "User",
            "credentials": {"identifier_field": "username_missing", "secret_field": "password_missing"}, # ERROR 5 & 6: Missing DB columns
            "route_guards": []
        })
    )
    
    print("Mock Broken SchemaBundle Created.")
    print("Running Validation Engine (Deterministic)...")
    
    engine = ValidationEngine()
    report = engine.execute(bundle, blueprint)
    
    print(f"\nValidation Result: VALID={report.is_valid}")
    print(f"Total Issues Found: {report.total_issues}")
    print("-" * 60)
    
    for i, issue in enumerate(report.issues, 1):
        print(f"[{str(issue.severity).upper()}] {str(issue.category).upper()} Issue #{i}")
        print(f"Source : {issue.source}")
        print(f"Target : {issue.target}")
        print(f"Message: {issue.message}")
        print(f"Hint   : {issue.repair_hint}")
        print("-" * 60)
        
    # Save output to a file
    with open("demo_validation_report.json", "w") as f:
        f.write(report.model_dump_json(indent=2))
    print("\nValidationReport written to demo_validation_report.json")

if __name__ == "__main__":
    run_demo()

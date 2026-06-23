"""
Verification script: tests all 14 data contracts with example JSON round-trips.
Run: python -m backend.tests.verify_contracts
"""

import json
import sys
from datetime import datetime, timezone


def main() -> None:
    from backend.schemas import (
        ArchitectureBlueprint,
        PipelineRequest,
        PipelineResponse,
        RepairReport,
        RuntimeResult,
        SchemaBundle,
        StructuredIntent,
        ValidationReport,
    )

    passed = 0
    failed = 0

    def test(name: str, model_class, data: dict) -> None:
        nonlocal passed, failed
        try:
            instance = model_class.model_validate(data)
            json_str = instance.model_dump_json()
            re_parsed = model_class.model_validate_json(json_str)
            assert instance == re_parsed, "Round-trip mismatch"
            print(f"  PASS  {name}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {name}: {e}")
            failed += 1

    print("=" * 60)
    print("Contract Round-Trip Verification")
    print("=" * 60)

    # 1. StructuredIntent
    test("StructuredIntent", StructuredIntent, {
        "app_name": "TaskFlow",
        "app_type": "web_application",
        "description": "A collaborative task management platform with deadline tracking",
        "target_users": ["admin", "team_lead", "team_member"],
        "core_features": [
            {"name": "task_management", "description": "Create and manage tasks", "priority": "critical"},
            {"name": "team_collab", "description": "Team collaboration features", "priority": "high"},
        ],
        "constraints": {"auth_required": True, "realtime": False, "file_uploads": False, "multi_tenancy": False, "i18n": False},
    })

    # 2. ArchitectureBlueprint
    test("ArchitectureBlueprint", ArchitectureBlueprint, {
        "entities": [
            {
                "name": "User",
                "description": "A registered user",
                "attributes": [
                    {"name": "id", "type": "uuid", "primary_key": True, "required": True, "unique": False, "description": "PK"},
                    {"name": "email", "type": "email", "primary_key": False, "required": True, "unique": True, "description": "Email"},
                ],
            },
            {
                "name": "Task",
                "description": "A work item",
                "attributes": [
                    {"name": "id", "type": "uuid", "primary_key": True, "required": True, "unique": False, "description": "PK"},
                    {"name": "title", "type": "string", "primary_key": False, "required": True, "unique": False, "description": "Title"},
                    {"name": "assignee_id", "type": "uuid", "primary_key": False, "required": False, "unique": False, "foreign_key": "User.id", "description": "Assignee"},
                ],
            },
        ],
        "roles": [
            {"name": "admin", "description": "Full access", "permissions": ["manage_users", "manage_tasks"]},
            {"name": "member", "description": "Basic access", "permissions": ["view_tasks"]},
        ],
        "pages": [
            {"name": "Dashboard", "route": "/dashboard", "description": "Main page", "auth_required": True, "allowed_roles": ["admin", "member"]},
        ],
        "features": [
            {"name": "task_crud", "description": "Task CRUD", "entities_involved": ["Task"], "operations": ["create", "read", "update", "delete"]},
        ],
        "flows": [
            {"name": "create_task", "description": "Create a task", "actor": "admin", "steps": ["Navigate to tasks", "Click create", "Fill form"], "preconditions": ["Authenticated"], "postconditions": ["Task created"]},
        ],
    })

    # 3-6. SchemaBundle (UI + API + DB + Auth)
    test("SchemaBundle", SchemaBundle, {
        "ui": {
            "pages": [{
                "name": "TaskBoard",
                "route": "/tasks",
                "layout": "sidebar",
                "auth_required": True,
                "allowed_roles": ["admin"],
                "components": [{
                    "type": "data_table",
                    "id": "task_list",
                    "data_source": "GET /api/tasks",
                    "columns": [{"field": "title", "label": "Title", "sortable": True, "filterable": False}],
                    "actions": ["create", "edit"],
                }],
            }],
        },
        "api": {
            "base_url": "/api",
            "endpoints": [{
                "method": "GET",
                "path": "/tasks",
                "description": "List tasks",
                "auth_required": True,
                "allowed_roles": ["admin"],
                "response": {"type": "paginated_list", "entity": "Task", "includes": ["assignee"], "status_code": 200},
            }],
        },
        "database": {
            "dialect": "sqlite",
            "tables": [{
                "name": "tasks",
                "entity": "Task",
                "columns": [
                    {"name": "id", "type": "TEXT", "primary_key": True, "nullable": False, "comment": "PK"},
                    {"name": "title", "type": "TEXT", "primary_key": False, "nullable": False, "comment": "Title"},
                ],
                "indexes": [{"name": "idx_tasks_title", "columns": ["title"], "unique": False}],
            }],
            "seed_data": {},
        },
        "auth": {
            "strategy": "jwt",
            "token_expiry_seconds": 3600,
            "refresh_token_enabled": True,
            "refresh_token_expiry_seconds": 604800,
            "user_entity": "User",
            "credentials": {"identifier_field": "email", "secret_field": "password_hash"},
            "roles": [{"name": "admin", "permissions": ["manage_users"]}],
            "route_guards": [{"route_pattern": "/api/admin/*", "allowed_roles": ["admin"]}],
        },
    })

    # 7. ValidationReport
    test("ValidationReport", ValidationReport, {
        "is_valid": False,
        "total_issues": 1,
        "error_count": 1,
        "warning_count": 0,
        "info_count": 0,
        "issues": [{
            "id": "val-001",
            "severity": "error",
            "category": "referential",
            "location": {"schema_layer": "api", "path": "endpoints[0]", "field": "entity", "context": "GET /tasks"},
            "message": "Entity 'Task' not found in architecture",
            "suggestion": "Add Task entity to blueprint",
            "auto_fixable": True,
        }],
    })

    # 8. RepairReport
    test("RepairReport", RepairReport, {
        "repair_iteration": 1,
        "issues_received": 1,
        "issues_fixed": 1,
        "issues_remaining": 0,
        "actions": [{
            "issue_id": "val-001",
            "action_type": "added_field",
            "strategy": "deterministic",
            "schema_layer": "api",
            "location": "endpoints[0]",
            "before_value": None,
            "after_value": "\"Task\"",
            "detail": "Added entity reference",
        }],
        "remaining_issues": [],
        "repaired_schema_bundle": {"ui": {}, "api": {}, "database": {}, "auth": {}},
    })

    # 9. RuntimeResult
    test("RuntimeResult", RuntimeResult, {
        "success": True,
        "database": {"dialect": "sqlite", "mode": "in_memory"},
        "tables_created": [
            {"name": "tasks", "column_count": 2, "status": "created", "error": None},
        ],
        "seed_data_results": [],
        "sample_queries": [
            {"description": "Count tables", "sql": "SELECT count(*) FROM sqlite_master WHERE type='table'", "expected_type": "count", "result": "1", "status": "passed", "error": None},
        ],
        "errors": [],
    })

    # 10. PipelineRequest
    test("PipelineRequest", PipelineRequest, {
        "prompt": "Build a task management app with teams and deadlines",
        "options": {"max_repair_iterations": 3, "include_seed_data": True, "target_database": "sqlite", "run_simulation": True, "verbose": False},
    })

    # 11. PipelineResponse
    test("PipelineResponse", PipelineResponse, {
        "pipeline_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "status": "success",
        "stages": {
            "s1_intent": {"name": "s1_intent", "status": "success", "duration_ms": 1200, "output": {}, "error": None},
            "s6_runtime": {"name": "s6_runtime", "status": "success", "duration_ms": 120, "output": {}, "error": None},
        },
        "final_config": {"ui": {}, "api": {}, "database": {}, "auth": {}},
        "metadata": {
            "total_duration_ms": 6870,
            "llm_calls_made": 6,
            "repair_iterations_used": 0,
            "input_prompt_length": 50,
            "output_token_estimate": 4200,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
    })

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

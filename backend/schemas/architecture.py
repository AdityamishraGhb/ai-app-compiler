"""
Stage 2 — Architecture Design: Data Contracts

Transforms a StructuredIntent into a full ArchitectureBlueprint defining
entities, roles, pages, features, and user flows.

Example JSON (ArchitectureBlueprint):
```json
{
    "entities": [
        {
            "name": "User",
            "description": "A registered user of the system",
            "attributes": [
                {
                    "name": "id",
                    "type": "uuid",
                    "primary_key": true,
                    "required": true,
                    "unique": false,
                    "foreign_key": null,
                    "enum_values": null,
                    "description": "Unique identifier"
                },
                {
                    "name": "email",
                    "type": "email",
                    "primary_key": false,
                    "required": true,
                    "unique": true,
                    "foreign_key": null,
                    "enum_values": null,
                    "description": "User email address"
                },
                {
                    "name": "role_id",
                    "type": "uuid",
                    "primary_key": false,
                    "required": true,
                    "unique": false,
                    "foreign_key": "Role.id",
                    "enum_values": null,
                    "description": "Reference to assigned role"
                }
            ]
        }
    ],
    "roles": [
        {
            "name": "admin",
            "description": "Full system access",
            "permissions": ["manage_users", "manage_teams", "manage_tasks"]
        }
    ],
    "pages": [
        {
            "name": "Dashboard",
            "route": "/dashboard",
            "description": "Main overview page with task statistics",
            "auth_required": true,
            "allowed_roles": ["admin", "team_lead", "team_member"]
        }
    ],
    "features": [
        {
            "name": "task_crud",
            "description": "Full CRUD operations on tasks",
            "entities_involved": ["Task"],
            "operations": ["create", "read", "update", "delete"]
        }
    ],
    "flows": [
        {
            "name": "create_task",
            "description": "End-to-end flow for creating a new task",
            "actor": "team_lead",
            "steps": [
                "User navigates to TaskBoard",
                "User clicks New Task button",
                "System displays task creation form",
                "User fills in title, description, priority, deadline",
                "System validates input",
                "System creates Task record",
                "System redirects to TaskDetail page"
            ],
            "preconditions": ["User is authenticated", "User has task creation permission"],
            "postconditions": ["Task record exists in database", "Assignee is notified"]
        }
    ]
}
```
"""

from pydantic import Field

from backend.schemas.common import StrictBaseModel
from backend.schemas.enums import CRUDOperation, FieldType


# ──────────────────────────────────────────────
#  Sub-models — Entities
# ──────────────────────────────────────────────

class EntityAttribute(StrictBaseModel):
    """A single attribute (column) of a logical entity."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Attribute name in snake_case.",
        examples=["id", "email", "created_at"],
    )
    type: FieldType = Field(
        ...,
        description="Logical data type (database-agnostic).",
    )
    primary_key: bool = Field(
        False,
        description="Whether this attribute is the entity's primary key.",
    )
    required: bool = Field(
        True,
        description="Whether this attribute is required (non-nullable).",
    )
    unique: bool = Field(
        False,
        description="Whether this attribute must be unique across all records.",
    )
    foreign_key: str | None = Field(
        None,
        description=(
            "Foreign key reference in 'Entity.attribute' format (e.g., 'Role.id'). "
            "None if this attribute is not a foreign key."
        ),
        pattern=r"^[A-Z][a-zA-Z0-9]*\.[a-z_]+$",
        examples=["Role.id", "User.id"],
    )
    enum_values: list[str] | None = Field(
        None,
        description="Allowed values when type is 'enum'. None for other types.",
        examples=[["todo", "in_progress", "done"]],
    )
    description: str = Field(
        "",
        max_length=300,
        description="Human-readable explanation of this attribute's purpose.",
    )


class Entity(StrictBaseModel):
    """A logical data entity (maps to a database table)."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Entity name in PascalCase (e.g., 'User', 'TaskComment').",
        examples=["User", "Task", "Team"],
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="What this entity represents in the domain.",
    )
    attributes: list[EntityAttribute] = Field(
        ...,
        min_length=1,
        description="Ordered list of attributes for this entity.",
    )


# ──────────────────────────────────────────────
#  Sub-models — Roles
# ──────────────────────────────────────────────

class RoleDefinition(StrictBaseModel):
    """A user role with its associated permissions."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Role identifier in snake_case.",
        examples=["admin", "team_lead", "team_member"],
    )
    description: str = Field(
        "",
        max_length=300,
        description="Human-readable description of this role's purpose.",
    )
    permissions: list[str] = Field(
        ...,
        min_length=1,
        description="List of permission identifiers granted to this role.",
        examples=[["manage_users", "manage_tasks", "view_reports"]],
    )


# ──────────────────────────────────────────────
#  Sub-models — Pages
# ──────────────────────────────────────────────

class PageDefinition(StrictBaseModel):
    """A UI page/screen in the application."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Page name in PascalCase (e.g., 'Dashboard', 'TaskBoard').",
        examples=["Dashboard", "TaskBoard", "LoginPage"],
    )
    route: str = Field(
        ...,
        min_length=1,
        description="URL route path for this page (e.g., '/dashboard', '/tasks/:id').",
        examples=["/dashboard", "/tasks/:id"],
    )
    description: str = Field(
        "",
        max_length=300,
        description="Purpose of this page.",
    )
    auth_required: bool = Field(
        True,
        description="Whether accessing this page requires authentication.",
    )
    allowed_roles: list[str] = Field(
        default_factory=list,
        description=(
            "Roles allowed to access this page. Empty list means all authenticated users. "
            "Values must match role names defined in `roles`."
        ),
    )


# ──────────────────────────────────────────────
#  Sub-models — Features
# ──────────────────────────────────────────────

class FeatureDefinition(StrictBaseModel):
    """A functional feature linking entities to CRUD operations."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Feature identifier in snake_case.",
        examples=["task_crud", "team_management"],
    )
    description: str = Field(
        "",
        max_length=500,
        description="What this feature enables.",
    )
    entities_involved: list[str] = Field(
        ...,
        min_length=1,
        description="Entity names (PascalCase) involved in this feature.",
        examples=[["Task", "User"]],
    )
    operations: list[CRUDOperation] = Field(
        ...,
        min_length=1,
        description="CRUD operations this feature supports.",
    )


# ──────────────────────────────────────────────
#  Sub-models — Flows
# ──────────────────────────────────────────────

class FlowDefinition(StrictBaseModel):
    """A user flow describing a sequence of actions through the application."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Flow identifier in snake_case.",
        examples=["create_task", "login", "assign_member"],
    )
    description: str = Field(
        "",
        max_length=500,
        description="Summary of what this flow accomplishes.",
    )
    actor: str = Field(
        ...,
        min_length=1,
        description="The user role that initiates this flow.",
        examples=["team_lead", "admin"],
    )
    steps: list[str] = Field(
        ...,
        min_length=2,
        description="Ordered, human-readable steps in the flow.",
    )
    preconditions: list[str] = Field(
        default_factory=list,
        description="Conditions that must be true before the flow starts.",
    )
    postconditions: list[str] = Field(
        default_factory=list,
        description="Conditions that must be true after the flow completes.",
    )


# ──────────────────────────────────────────────
#  Stage 2 Output
# ──────────────────────────────────────────────

class ArchitectureBlueprint(StrictBaseModel):
    """
    **Stage 2 Output** — The complete logical architecture of the application.

    Produced by: `s2_architecture/designer.py`
    Consumed by: `s3_schema/generator.py` (all 4 sub-generators)

    This is the single source of truth for entity names, role names,
    and page routes. All downstream schemas (UI, API, DB, Auth) must
    reference identifiers defined here — enabling cross-layer validation.
    """

    entities: list[Entity] = Field(
        ...,
        min_length=1,
        description=(
            "All domain entities. Entity names are the canonical identifiers "
            "referenced by API endpoints, DB tables, and UI components."
        ),
    )
    roles: list[RoleDefinition] = Field(
        ...,
        min_length=1,
        description=(
            "All user roles. Role names are referenced by pages, API endpoints, "
            "and auth route guards."
        ),
    )
    pages: list[PageDefinition] = Field(
        ...,
        min_length=1,
        description="All UI pages/screens in the application.",
    )
    features: list[FeatureDefinition] = Field(
        ...,
        min_length=1,
        description="Functional features linking entities to operations.",
    )
    flows: list[FlowDefinition] = Field(
        default_factory=list,
        description="User flows describing key user journeys through the application.",
    )

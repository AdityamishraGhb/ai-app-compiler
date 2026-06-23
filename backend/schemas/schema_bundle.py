"""
Stage 3 — Schema Generation: Data Contracts

Generates four concrete, implementation-ready schemas from the
ArchitectureBlueprint, bundled together as a SchemaBundle.

Contains:
- UISchema        — Pages, components, form fields, data bindings
- APISchema       — REST endpoints, params, request/response shapes
- DatabaseSchema   — SQLite tables, columns, indexes, foreign keys, seed data
- AuthSchema       — Strategy, roles, permissions, route guards
- SchemaBundle     — Composite of all four

──────────────────────────────────────────────────────────────────
Example JSON (UISchema):
```json
{
    "pages": [
        {
            "name": "TaskBoard",
            "route": "/tasks",
            "layout": "sidebar",
            "auth_required": true,
            "allowed_roles": ["admin", "team_lead", "team_member"],
            "components": [
                {
                    "type": "data_table",
                    "id": "task_list",
                    "data_source": "GET /api/tasks",
                    "columns": [
                        {"field": "title", "label": "Title", "sortable": true, "filterable": false},
                        {"field": "status", "label": "Status", "sortable": true, "filterable": true}
                    ],
                    "actions": ["create", "edit", "delete"],
                    "fields": []
                }
            ]
        }
    ]
}
```

Example JSON (APISchema):
```json
{
    "base_url": "/api",
    "endpoints": [
        {
            "method": "GET",
            "path": "/tasks",
            "description": "List all tasks for the authenticated user",
            "auth_required": true,
            "allowed_roles": ["admin", "team_lead", "team_member"],
            "path_params": [],
            "query_params": [
                {"name": "status", "type": "string", "required": false, "default": null, "enum_values": ["todo", "in_progress", "done"], "description": "Filter by status"}
            ],
            "request_body": null,
            "response": {
                "type": "paginated_list",
                "entity": "Task",
                "includes": ["assignee", "team"],
                "status_code": 200,
                "fields": null
            }
        }
    ]
}
```

Example JSON (DatabaseSchema):
```json
{
    "dialect": "sqlite",
    "tables": [
        {
            "name": "tasks",
            "entity": "Task",
            "columns": [
                {"name": "id", "type": "TEXT", "primary_key": true, "nullable": false, "unique": false, "default": null, "check": null, "foreign_key": null, "comment": "UUID primary key"},
                {"name": "title", "type": "TEXT", "primary_key": false, "nullable": false, "unique": false, "default": null, "check": null, "foreign_key": null, "comment": "Task title"},
                {"name": "status", "type": "TEXT", "primary_key": false, "nullable": false, "unique": false, "default": "'todo'", "check": "status IN ('todo', 'in_progress', 'done')", "foreign_key": null, "comment": "Current status"}
            ],
            "indexes": [
                {"name": "idx_tasks_status", "columns": ["status"], "unique": false}
            ],
            "composite_primary_key": null
        }
    ],
    "seed_data": {
        "roles": [
            {"id": "role-admin", "name": "admin", "permissions": "[\"manage_users\"]"}
        ]
    }
}
```

Example JSON (AuthSchema):
```json
{
    "strategy": "jwt",
    "token_expiry_seconds": 3600,
    "refresh_token_enabled": true,
    "refresh_token_expiry_seconds": 604800,
    "user_entity": "User",
    "credentials": {
        "identifier_field": "email",
        "secret_field": "password_hash"
    },
    "roles": [
        {
            "name": "admin",
            "permissions": ["manage_users", "manage_teams"]
        }
    ],
    "route_guards": [
        {
            "route_pattern": "/api/admin/*",
            "method": null,
            "allowed_roles": ["admin"],
            "description": "Admin-only routes"
        }
    ]
}
```

Example JSON (SchemaBundle):
```json
{
    "ui": { "...UISchema..." },
    "api": { "...APISchema..." },
    "database": { "...DatabaseSchema..." },
    "auth": { "...AuthSchema..." }
}
```
"""

from __future__ import annotations

from pydantic import Field

from backend.schemas.common import StrictBaseModel
from backend.schemas.enums import (
    AuthStrategy,
    HTTPMethod,
    APIParamType,
    PageLayout,
    ResponseType,
    SQLiteColumnType,
    UIComponentType,
    UIFieldType,
)


# ══════════════════════════════════════════════
#  UI SCHEMA
# ══════════════════════════════════════════════

class UITableColumn(StrictBaseModel):
    """A column definition for a data_table component."""

    field: str = Field(
        ...,
        min_length=1,
        description=(
            "Dot-notation path to the data field (e.g., 'title', 'assignee.name'). "
            "Nested paths imply a relationship include on the API side."
        ),
        examples=["title", "status", "assignee.name"],
    )
    label: str = Field(
        ...,
        min_length=1,
        description="Human-readable column header.",
    )
    sortable: bool = Field(
        False,
        description="Whether the column supports sorting.",
    )
    filterable: bool = Field(
        False,
        description="Whether the column supports filtering.",
    )


class UIFormField(StrictBaseModel):
    """A field within a form or modal_form component."""

    name: str = Field(
        ...,
        min_length=1,
        description="Field name matching the entity attribute or API request body field.",
        examples=["title", "email", "priority"],
    )
    type: UIFieldType = Field(
        ...,
        description="Input widget type.",
    )
    label: str = Field(
        "",
        description="Display label. Defaults to humanized field name if empty.",
    )
    required: bool = Field(
        False,
        description="Whether the field must be filled.",
    )
    default: str | int | float | bool | None = Field(
        None,
        description="Default value for the field.",
    )
    placeholder: str = Field(
        "",
        description="Placeholder text.",
    )
    max_length: int | None = Field(
        None,
        ge=1,
        description="Maximum character length for text inputs.",
    )
    options: list[str] | None = Field(
        None,
        description="Allowed values for select/radio/multi_select field types.",
    )
    entity: str | None = Field(
        None,
        description=(
            "Entity name for entity_select fields. Must match an entity "
            "in the ArchitectureBlueprint."
        ),
    )


class UIComponent(StrictBaseModel):
    """A UI component rendered on a page."""

    type: UIComponentType = Field(
        ...,
        description="Component type determining rendering behavior.",
    )
    id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique component identifier within the page (e.g., 'task_list', 'create_task_form').",
    )
    data_source: str | None = Field(
        None,
        description=(
            "API endpoint this component binds to, in 'METHOD /path' format "
            "(e.g., 'GET /api/tasks'). Required for data-driven components."
        ),
        examples=["GET /api/tasks", "POST /api/tasks"],
    )
    columns: list[UITableColumn] = Field(
        default_factory=list,
        description="Column definitions for data_table components.",
    )
    fields: list[UIFormField] = Field(
        default_factory=list,
        description="Field definitions for form/modal_form components.",
    )
    actions: list[str] = Field(
        default_factory=list,
        description="Action buttons available (e.g., ['create', 'edit', 'delete']).",
    )
    submit_endpoint: str | None = Field(
        None,
        description="API endpoint for form submission (e.g., 'POST /api/tasks').",
    )
    trigger: str | None = Field(
        None,
        description="Component.action that opens this component (e.g., 'task_list.create').",
    )


class UIPage(StrictBaseModel):
    """A full page definition in the UI schema."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Page name in PascalCase. Must match a page in ArchitectureBlueprint.",
        examples=["TaskBoard", "Dashboard", "LoginPage"],
    )
    route: str = Field(
        ...,
        min_length=1,
        description="URL route for this page.",
        examples=["/tasks", "/dashboard", "/login"],
    )
    layout: PageLayout = Field(
        PageLayout.SIDEBAR,
        description="Layout template for the page.",
    )
    auth_required: bool = Field(
        True,
        description="Whether this page requires authentication.",
    )
    allowed_roles: list[str] = Field(
        default_factory=list,
        description="Roles that can access this page. Empty list = all authenticated users.",
    )
    components: list[UIComponent] = Field(
        ...,
        min_length=1,
        description="UI components rendered on this page.",
    )


class UISchema(StrictBaseModel):
    """
    **Stage 3 Sub-output** — Complete UI schema defining pages and components.

    Cross-layer references:
    - `UIPage.name` → must exist in ArchitectureBlueprint.pages
    - `UIComponent.data_source` → must match an APISchema endpoint
    - `UIFormField.entity` → must exist in ArchitectureBlueprint.entities
    - `UIPage.allowed_roles` → must exist in ArchitectureBlueprint.roles
    """

    pages: list[UIPage] = Field(
        ...,
        min_length=1,
        description="All pages in the application UI.",
    )


# ══════════════════════════════════════════════
#  API SCHEMA
# ══════════════════════════════════════════════

class APIParam(StrictBaseModel):
    """A query or path parameter for an API endpoint."""

    name: str = Field(
        ...,
        min_length=1,
        description="Parameter name.",
        examples=["status", "page", "limit", "id"],
    )
    type: APIParamType = Field(
        ...,
        description="Data type of the parameter.",
    )
    required: bool = Field(
        False,
        description="Whether this parameter is required.",
    )
    default: str | int | float | bool | None = Field(
        None,
        description="Default value if not provided.",
    )
    enum_values: list[str] | None = Field(
        None,
        description="Allowed values for enum-like parameters.",
    )
    description: str = Field(
        "",
        max_length=300,
        description="Parameter description.",
    )


class APIRequestBody(StrictBaseModel):
    """Request body schema for POST/PUT/PATCH endpoints."""

    entity: str | None = Field(
        None,
        description="Entity name this request body maps to. Must match ArchitectureBlueprint.",
        examples=["Task", "User"],
    )
    fields: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "Field names accepted in the request body. Must be valid attribute "
            "names for the referenced entity."
        ),
    )


class APIResponse(StrictBaseModel):
    """Response shape for an API endpoint."""

    type: ResponseType = Field(
        ...,
        description="Shape of the response (single object, list, paginated list, or empty).",
    )
    entity: str | None = Field(
        None,
        description="Entity name this response returns. Must match ArchitectureBlueprint.",
        examples=["Task", "User"],
    )
    includes: list[str] = Field(
        default_factory=list,
        description=(
            "Related entities to include in the response (e.g., ['assignee', 'team']). "
            "Enables nested object resolution."
        ),
    )
    status_code: int = Field(
        200,
        ge=100,
        le=599,
        description="HTTP status code for successful responses.",
    )
    fields: list[str] | None = Field(
        None,
        description="Explicit field list for non-entity responses (e.g., auth tokens).",
    )


class APIEndpoint(StrictBaseModel):
    """A single REST API endpoint definition."""

    method: HTTPMethod = Field(
        ...,
        description="HTTP method.",
    )
    path: str = Field(
        ...,
        min_length=1,
        description="Endpoint path relative to base_url (e.g., '/tasks', '/tasks/{id}').",
        examples=["/tasks", "/tasks/{id}", "/auth/login"],
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="What this endpoint does.",
    )
    auth_required: bool = Field(
        True,
        description="Whether this endpoint requires authentication.",
    )
    allowed_roles: list[str] = Field(
        default_factory=list,
        description="Roles allowed to call this endpoint. Empty = all authenticated users.",
    )
    path_params: list[APIParam] = Field(
        default_factory=list,
        description="URL path parameters (e.g., {id}).",
    )
    query_params: list[APIParam] = Field(
        default_factory=list,
        description="URL query string parameters.",
    )
    request_body: APIRequestBody | None = Field(
        None,
        description="Request body schema. None for GET/DELETE endpoints.",
    )
    response: APIResponse = Field(
        ...,
        description="Response shape and entity.",
    )


class APISchema(StrictBaseModel):
    """
    **Stage 3 Sub-output** — Complete REST API schema.

    Cross-layer references:
    - `APIEndpoint.allowed_roles` → must exist in ArchitectureBlueprint.roles
    - `APIRequestBody.entity` → must exist in ArchitectureBlueprint.entities
    - `APIRequestBody.fields` → must be valid attributes of the entity
    - `APIResponse.entity` → must exist in ArchitectureBlueprint.entities
    - `APIResponse.includes` → must be valid relationship names
    """

    base_url: str = Field(
        "/api",
        description="Base URL prefix for all endpoints.",
    )
    endpoints: list[APIEndpoint] = Field(
        ...,
        min_length=1,
        description="All REST endpoints.",
    )


# ══════════════════════════════════════════════
#  DATABASE SCHEMA
# ══════════════════════════════════════════════

class ForeignKeyRef(StrictBaseModel):
    """A foreign key reference to another table."""

    table: str = Field(
        ...,
        min_length=1,
        description="Referenced table name.",
        examples=["users", "roles", "teams"],
    )
    column: str = Field(
        ...,
        min_length=1,
        description="Referenced column in the target table.",
        examples=["id"],
    )


class DBColumn(StrictBaseModel):
    """A column definition in a database table."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Column name in snake_case.",
        examples=["id", "title", "created_at"],
    )
    type: SQLiteColumnType = Field(
        ...,
        description="SQLite column type affinity.",
    )
    primary_key: bool = Field(
        False,
        description="Whether this column is the single primary key.",
    )
    nullable: bool = Field(
        True,
        description="Whether this column allows NULL values.",
    )
    unique: bool = Field(
        False,
        description="Whether this column has a UNIQUE constraint.",
    )
    default: str | None = Field(
        None,
        description=(
            "SQL default value expression as a string. "
            "Use SQL literal syntax (e.g., \"'todo'\" for text, \"0\" for integer)."
        ),
    )
    check: str | None = Field(
        None,
        description=(
            "SQL CHECK constraint expression. "
            "e.g., \"status IN ('todo', 'in_progress', 'done')\""
        ),
    )
    foreign_key: ForeignKeyRef | None = Field(
        None,
        description="Foreign key reference. None if column is not a foreign key.",
    )
    comment: str = Field(
        "",
        max_length=300,
        description="Developer-facing comment explaining this column.",
    )


class DBIndex(StrictBaseModel):
    """An index on one or more columns of a database table."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Index name (conventionally idx_{table}_{columns}).",
        examples=["idx_tasks_status", "idx_users_email"],
    )
    columns: list[str] = Field(
        ...,
        min_length=1,
        description="Column names in the index.",
    )
    unique: bool = Field(
        False,
        description="Whether this is a unique index.",
    )


class DBTable(StrictBaseModel):
    """A database table definition."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description=(
            "Table name in snake_case plural (e.g., 'users', 'tasks'). "
            "Convention: lowercase plural of the entity name."
        ),
        examples=["users", "tasks", "team_members"],
    )
    entity: str = Field(
        ...,
        min_length=1,
        description="Entity name (PascalCase) this table represents. Must match ArchitectureBlueprint.",
        examples=["User", "Task", "TeamMember"],
    )
    columns: list[DBColumn] = Field(
        ...,
        min_length=1,
        description="Column definitions for this table.",
    )
    indexes: list[DBIndex] = Field(
        default_factory=list,
        description="Indexes on this table.",
    )
    composite_primary_key: list[str] | None = Field(
        None,
        description=(
            "Column names forming a composite primary key. "
            "Use this instead of per-column primary_key for junction tables."
        ),
        examples=[["team_id", "user_id"]],
    )


class DatabaseSchema(StrictBaseModel):
    """
    **Stage 3 Sub-output** — Complete database schema for SQLite.

    Cross-layer references:
    - `DBTable.entity` → must exist in ArchitectureBlueprint.entities
    - `DBColumn.foreign_key.table` → must be a valid table name in this schema
    - Column names → should correspond to entity attributes
    """

    dialect: str = Field(
        "sqlite",
        description="SQL dialect. Currently always 'sqlite'.",
    )
    tables: list[DBTable] = Field(
        ...,
        min_length=1,
        description="All database tables.",
    )
    seed_data: dict[str, list[dict[str, str | int | float | bool | None]]] = Field(
        default_factory=dict,
        description=(
            "Seed data keyed by table name. Each value is a list of row dicts. "
            "Used for initial data like default roles."
        ),
    )


# ══════════════════════════════════════════════
#  AUTH SCHEMA
# ══════════════════════════════════════════════

class AuthCredentials(StrictBaseModel):
    """Credential field mapping for authentication."""

    identifier_field: str = Field(
        ...,
        min_length=1,
        description="Entity attribute used as the login identifier (e.g., 'email').",
        examples=["email", "username"],
    )
    secret_field: str = Field(
        ...,
        min_length=1,
        description="Entity attribute storing the hashed secret (e.g., 'password_hash').",
        examples=["password_hash"],
    )


class AuthRole(StrictBaseModel):
    """A role definition within the auth schema."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Role name. Must match a role in ArchitectureBlueprint.roles.",
    )
    permissions: list[str] = Field(
        ...,
        min_length=1,
        description="Permission identifiers granted to this role.",
    )


class RouteGuard(StrictBaseModel):
    """An access control rule protecting a route pattern."""

    route_pattern: str = Field(
        ...,
        min_length=1,
        description="Route pattern to protect. Supports wildcards (e.g., '/api/admin/*').",
        examples=["/api/admin/*", "/api/tasks"],
    )
    method: HTTPMethod | None = Field(
        None,
        description="Specific HTTP method to guard. None means all methods.",
    )
    allowed_roles: list[str] = Field(
        ...,
        min_length=1,
        description="Roles allowed to access this route.",
    )
    description: str = Field(
        "",
        max_length=300,
        description="Purpose of this route guard.",
    )


class AuthSchema(StrictBaseModel):
    """
    **Stage 3 Sub-output** — Authentication and authorization schema.

    Cross-layer references:
    - `user_entity` → must exist in ArchitectureBlueprint.entities
    - `AuthRole.name` → must match ArchitectureBlueprint.roles
    - `AuthCredentials.identifier_field` → must be an attribute of user_entity
    - `RouteGuard.allowed_roles` → must be valid role names
    - `RouteGuard.route_pattern` → should match APISchema endpoint paths
    """

    strategy: AuthStrategy = Field(
        AuthStrategy.JWT,
        description="Authentication strategy.",
    )
    token_expiry_seconds: int = Field(
        3600,
        ge=60,
        le=86400,
        description="Access token lifetime in seconds.",
    )
    refresh_token_enabled: bool = Field(
        True,
        description="Whether refresh tokens are issued.",
    )
    refresh_token_expiry_seconds: int = Field(
        604800,
        ge=3600,
        le=2592000,
        description="Refresh token lifetime in seconds (default: 7 days).",
    )
    user_entity: str = Field(
        "User",
        min_length=1,
        description="Entity name representing the authenticatable user.",
    )
    credentials: AuthCredentials = Field(
        ...,
        description="Field mapping for login credentials.",
    )
    roles: list[AuthRole] = Field(
        ...,
        min_length=1,
        description="Role definitions with their permissions.",
    )
    route_guards: list[RouteGuard] = Field(
        default_factory=list,
        description="Access control rules for API routes.",
    )


# ══════════════════════════════════════════════
#  SCHEMA BUNDLE (Composite)
# ══════════════════════════════════════════════

class SchemaBundle(StrictBaseModel):
    """
    **Stage 3 Output** — Composite of all four generated schemas.

    Produced by: `s3_schema/generator.py`
    Consumed by: `s4_validation/engine.py`, `s5_repair/engine.py`, `s6_runtime/simulator.py`

    The SchemaBundle is the central artifact that validation, repair,
    and runtime simulation all operate on. Each sub-schema is independently
    generated but must be cross-layer consistent.
    """

    ui: UISchema = Field(
        ...,
        description="UI page and component definitions.",
    )
    api: APISchema = Field(
        ...,
        description="REST API endpoint definitions.",
    )
    database: DatabaseSchema = Field(
        ...,
        description="Database table and column definitions.",
    )
    auth: AuthSchema = Field(
        ...,
        description="Authentication and authorization definitions.",
    )

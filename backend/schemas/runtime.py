"""
Stage 6 — Runtime Simulation: Data Contracts

Executes the DatabaseSchema against an in-memory SQLite instance to
verify that the generated schema is actually executable.

Example JSON (RuntimeResult):
```json
{
    "success": true,
    "database": {
        "dialect": "sqlite",
        "mode": "in_memory"
    },
    "tables_created": [
        {"name": "roles", "column_count": 3, "status": "created", "error": null},
        {"name": "users", "column_count": 6, "status": "created", "error": null},
        {"name": "teams", "column_count": 3, "status": "created", "error": null},
        {"name": "team_members", "column_count": 2, "status": "created", "error": null},
        {"name": "tasks", "column_count": 10, "status": "created", "error": null},
        {"name": "comments", "column_count": 5, "status": "created", "error": null}
    ],
    "seed_data_results": [
        {"table": "roles", "rows_inserted": 3, "status": "passed", "error": null}
    ],
    "sample_queries": [
        {
            "description": "Count all tables",
            "sql": "SELECT count(*) FROM sqlite_master WHERE type='table'",
            "expected_type": "count",
            "result": "6",
            "status": "passed",
            "error": null
        },
        {
            "description": "Verify foreign keys on tasks table",
            "sql": "PRAGMA foreign_key_list('tasks')",
            "expected_type": "pragma",
            "result": "[{\"table\": \"users\", \"from\": \"assignee_id\", \"to\": \"id\"}, {\"table\": \"users\", \"from\": \"created_by\", \"to\": \"id\"}, {\"table\": \"teams\", \"from\": \"team_id\", \"to\": \"id\"}]",
            "status": "passed",
            "error": null
        }
    ],
    "errors": []
}
```
"""

from pydantic import Field

from backend.schemas.common import StrictBaseModel
from backend.schemas.enums import QueryStatus, TableCreationStatus


# ──────────────────────────────────────────────
#  Sub-models
# ──────────────────────────────────────────────

class DatabaseInfo(StrictBaseModel):
    """Metadata about the SQLite instance used for simulation."""

    dialect: str = Field(
        "sqlite",
        description="Database dialect.",
    )
    mode: str = Field(
        "in_memory",
        description="Database mode (always 'in_memory' for simulation).",
    )


class TableCreationResult(StrictBaseModel):
    """Result of attempting to CREATE TABLE in SQLite."""

    name: str = Field(
        ...,
        min_length=1,
        description="Table name.",
    )
    column_count: int = Field(
        ...,
        ge=0,
        description="Number of columns in the CREATE TABLE statement.",
    )
    status: TableCreationStatus = Field(
        ...,
        description="Whether the table was successfully created.",
    )
    error: str | None = Field(
        None,
        description="Error message if creation failed.",
    )


class SeedDataResult(StrictBaseModel):
    """Result of inserting seed data into a table."""

    table: str = Field(
        ...,
        min_length=1,
        description="Table name that received seed data.",
    )
    rows_inserted: int = Field(
        ...,
        ge=0,
        description="Number of rows successfully inserted.",
    )
    status: QueryStatus = Field(
        ...,
        description="Whether seed insertion succeeded.",
    )
    error: str | None = Field(
        None,
        description="Error message if insertion failed.",
    )


class SampleQueryResult(StrictBaseModel):
    """Result of executing a verification query against the simulated database."""

    description: str = Field(
        ...,
        min_length=1,
        description="Human-readable description of what this query verifies.",
    )
    sql: str = Field(
        ...,
        min_length=1,
        description="The SQL statement executed.",
    )
    expected_type: str = Field(
        ...,
        min_length=1,
        description="Expected result type (e.g., 'count', 'rows', 'pragma', 'boolean').",
        examples=["count", "rows", "pragma", "boolean"],
    )
    result: str | None = Field(
        None,
        description="JSON-serialized query result. None if query failed.",
    )
    status: QueryStatus = Field(
        ...,
        description="Whether the query executed successfully and produced expected results.",
    )
    error: str | None = Field(
        None,
        description="Error message if query failed.",
    )


class RuntimeError_(StrictBaseModel):
    """A runtime error encountered during simulation."""

    phase: str = Field(
        ...,
        min_length=1,
        description="Phase where the error occurred (e.g., 'table_creation', 'seed_data', 'sample_query').",
        examples=["table_creation", "seed_data", "sample_query"],
    )
    table: str | None = Field(
        None,
        description="Table involved, if applicable.",
    )
    message: str = Field(
        ...,
        min_length=1,
        description="Error description.",
    )
    sql: str | None = Field(
        None,
        description="The SQL statement that failed, if applicable.",
    )


# ──────────────────────────────────────────────
#  Stage 6 Output
# ──────────────────────────────────────────────

class RuntimeResult(StrictBaseModel):
    """
    **Stage 6 Output** — Results from executing the database schema in SQLite.

    Produced by: `s6_runtime/simulator.py`
    Consumed by: Pipeline response (final output)

    Success means all tables were created, seed data was inserted,
    and all sample queries passed.
    """

    success: bool = Field(
        ...,
        description="True if all tables created, all seed data inserted, and all queries passed.",
    )
    database: DatabaseInfo = Field(
        default_factory=DatabaseInfo,
        description="Database metadata.",
    )
    tables_created: list[TableCreationResult] = Field(
        default_factory=list,
        description="Results for each CREATE TABLE statement.",
    )
    seed_data_results: list[SeedDataResult] = Field(
        default_factory=list,
        description="Results for seed data insertion per table.",
    )
    sample_queries: list[SampleQueryResult] = Field(
        default_factory=list,
        description="Results from verification queries.",
    )
    errors: list[RuntimeError_] = Field(
        default_factory=list,
        description="All errors encountered during simulation.",
    )

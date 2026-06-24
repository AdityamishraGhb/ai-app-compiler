"""
Stage 5 — Repair Engine: Data Contracts

Takes a SchemaBundle and its ValidationReport, then surgically repairs
only the failing sections. Uses deterministic fixes first, then
targeted LLM calls for semantic repairs.

Example JSON (RepairReport):
```json
{
    "repair_iteration": 1,
    "issues_received": 2,
    "issues_fixed": 2,
    "issues_remaining": 0,
    "actions": [
        {
            "issue_id": "val-001",
            "action_type": "removed_field",
            "strategy": "deterministic",
            "schema_layer": "api",
            "location": "endpoints[3].request_body.fields",
            "before_value": "[\"title\", \"description\", \"status\", \"priority\", \"deadline\", \"assignee_id\", \"team_id\"]",
            "after_value": "[\"title\", \"description\", \"status\", \"priority\", \"deadline\", \"assignee_id\"]",
            "detail": "Removed 'team_id' from PUT /tasks/{id} request body — team assignment is immutable after creation"
        },
        {
            "issue_id": "val-002",
            "action_type": "added_include",
            "strategy": "deterministic",
            "schema_layer": "api",
            "location": "endpoints[0].response.includes",
            "before_value": "[\"team\"]",
            "after_value": "[\"team\", \"assignee\"]",
            "detail": "Added 'assignee' to GET /api/tasks response includes to resolve UI nested field 'assignee.name'"
        }
    ],
    "remaining_issues": [],
    "repaired_schema_bundle": { "...patched SchemaBundle..." }
}
```
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from backend.schemas.common import StrictBaseModel
from backend.schemas.enums import RepairActionType, RepairStrategy, SchemaLayerName
from backend.schemas.validation import ValidationIssue

if TYPE_CHECKING:
    from backend.schemas.schema_bundle import SchemaBundle


# ──────────────────────────────────────────────
#  Sub-models
# ──────────────────────────────────────────────

class RepairAction(StrictBaseModel):
    """
    Record of a single attempted repair action during Stage 5.
    """
    issue_id: str = Field(
        ...,
        description="The ValidationIssue.id that prompted this repair attempt.",
    )
    component_modified: str = Field(
        ...,
        description="The component or schema layer that was modified (e.g. 'DatabaseSchema', 'APISchema').",
    )
    strategy_used: str = Field(
        ...,
        description="The strategy used (e.g., 'LLM_REGENERATION', 'DETERMINISTIC_FIX').",
    )
    success: bool = Field(
        ...,
        description="Whether the issue was successfully fixed.",
    )
    before_hash: str | None = Field(
        None,
        description="Hash of the schema state before the repair.",
    )
    after_hash: str | None = Field(
        None,
        description="Hash of the schema state after the repair.",
    )


# ──────────────────────────────────────────────
#  Stage 5 Output
# ──────────────────────────────────────────────

class RepairReport(StrictBaseModel):
    """
    Summary of all repairs executed during Stage 5.
    """
    issues_received: int = Field(
        ...,
        description="Number of issues passed into the Repair Engine.",
    )
    issues_fixed: int = Field(
        ...,
        description="Number of issues successfully resolved.",
    )
    issues_remaining: int = Field(
        ...,
        description="Number of issues that could not be resolved.",
    )
    repair_success_rate: float = Field(
        ...,
        description="Percentage of issues successfully fixed (0.0 to 100.0).",
    )
    repair_actions: list[RepairAction] = Field(
        default_factory=list,
        description="Detailed log of all repair attempts.",
    )

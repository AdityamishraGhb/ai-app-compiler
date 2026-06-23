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
    A single repair action applied to fix a ValidationIssue.

    Each action records the before/after state for auditability.
    """

    issue_id: str = Field(
        ...,
        min_length=1,
        description="ID of the ValidationIssue this action addresses (e.g., 'val-001').",
        examples=["val-001", "val-012"],
    )
    action_type: RepairActionType = Field(
        ...,
        description="Type of modification made.",
    )
    strategy: RepairStrategy = Field(
        ...,
        description=(
            "'deterministic' for rule-based fixes (missing defaults, type coercion); "
            "'llm_assisted' for semantic repairs requiring context understanding."
        ),
    )
    schema_layer: SchemaLayerName = Field(
        ...,
        description="Which schema layer was modified.",
    )
    location: str = Field(
        ...,
        min_length=1,
        description="JSON-path-like location of the modification.",
        examples=["endpoints[3].request_body.fields", "tables[2].columns"],
    )
    before_value: str | None = Field(
        None,
        description="JSON-serialized value before repair. None for additions.",
    )
    after_value: str | None = Field(
        None,
        description="JSON-serialized value after repair. None for deletions.",
    )
    detail: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Human-readable explanation of what was changed and why.",
    )


# ──────────────────────────────────────────────
#  Stage 5 Output
# ──────────────────────────────────────────────

class RepairReport(StrictBaseModel):
    """
    **Stage 5 Output** — Report of all repairs applied to the SchemaBundle.

    Produced by: `s5_repair/engine.py`
    Consumed by: `s4_validation/engine.py` (re-validation loop) or `s6_runtime/simulator.py`

    If `issues_remaining > 0`, the orchestrator may send the repaired bundle
    back to Stage 4 for re-validation (up to max_repair_iterations).
    """

    repair_iteration: int = Field(
        ...,
        ge=1,
        description="Which iteration of the repair loop this report represents (1-indexed).",
    )
    issues_received: int = Field(
        ...,
        ge=0,
        description="Number of issues passed to the repair engine for this iteration.",
    )
    issues_fixed: int = Field(
        ...,
        ge=0,
        description="Number of issues successfully fixed in this iteration.",
    )
    issues_remaining: int = Field(
        ...,
        ge=0,
        description="Number of issues that could not be fixed (remaining for next iteration or user).",
    )
    actions: list[RepairAction] = Field(
        default_factory=list,
        description="All repair actions applied in this iteration.",
    )
    remaining_issues: list[ValidationIssue] = Field(
        default_factory=list,
        description="Issues that could not be repaired. Forwarded to next iteration or flagged to user.",
    )

    # NOTE: `repaired_schema_bundle` is typed as Any here to avoid a circular
    # import.  At runtime the orchestrator passes the actual SchemaBundle.
    # We use model_rebuild() in __init__.py to resolve the forward reference.
    repaired_schema_bundle: dict = Field(
        ...,
        description=(
            "The patched SchemaBundle as a dict. The orchestrator deserializes "
            "this back into a SchemaBundle for re-validation or runtime."
        ),
    )

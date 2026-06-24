"""
Stage 4 — Validation Engine: Data Contracts

The validation engine inspects a SchemaBundle for structural, referential,
and logical issues WITHOUT using an LLM. All checks are deterministic.

Example JSON (ValidationReport):
```json
{
    "is_valid": false,
    "total_issues": 2,
    "error_count": 1,
    "warning_count": 1,
    "info_count": 0,
    "issues": [
        {
            "id": "val-001",
            "severity": "error",
            "category": "referential",
            "location": {
                "schema_layer": "api",
                "path": "endpoints[3].request_body.fields",
                "field": "team_id",
                "context": "PUT /tasks/{id}"
            },
            "message": "API endpoint PUT /tasks/{id} includes 'team_id' in writable fields but entity 'Task' marks 'team_id' as immutable after creation",
            "suggestion": "Remove 'team_id' from PUT request body or add it as an updatable field in the entity definition",
            "auto_fixable": true
        },
        {
            "id": "val-002",
            "severity": "warning",
            "category": "logical",
            "location": {
                "schema_layer": "ui",
                "path": "pages[0].components[0].columns[4]",
                "field": "assignee.name",
                "context": "TaskBoard → task_list"
            },
            "message": "UI column references nested field 'assignee.name' but GET /api/tasks response does not include 'assignee' in its includes list",
            "suggestion": "Add 'assignee' to the includes array of the GET /api/tasks endpoint response",
            "auto_fixable": true
        }
    ]
}
```
"""

from pydantic import Field, model_validator

from backend.schemas.common import StrictBaseModel
from backend.schemas.enums import (
    SchemaLayerName,
    ValidationCategory,
    ValidationSeverity,
)


# ──────────────────────────────────────────────
#  Sub-models
# ──────────────────────────────────────────────

class ValidationIssue(StrictBaseModel):
    """
    A single validation issue found in the SchemaBundle.
    """
    id: str = Field(
        "",
        description="Unique identifier for the issue (e.g., 'val-1').",
    )
    severity: ValidationSeverity = Field(
        ...,
        description="Issue severity. 'error' blocks runtime; 'warning' is advisory.",
    )
    category: ValidationCategory = Field(
        ...,
        description="Issue category (e.g. 'referential', 'logical').",
    )
    source: str = Field(
        ...,
        description="The source of the reference (e.g., 'APIEndpoint[GET /users].response.entity').",
    )
    target: str = Field(
        ...,
        description="The expected target that is missing or mismatched (e.g., 'DBTable[User]').",
    )
    message: str = Field(
        ...,
        description="Human-readable description of the issue.",
    )
    repair_hint: str = Field(
        "",
        description="Actionable hint for the RepairEngine to fix the issue.",
    )


# ──────────────────────────────────────────────
#  Stage 4 Output
# ──────────────────────────────────────────────

class ValidationReport(StrictBaseModel):
    """
    **Stage 4 Output** — Complete validation report for a SchemaBundle.

    Produced by: `s4_validation/engine.py`
    Consumed by: `s5_repair/engine.py` (if `is_valid` is False)

    The `is_valid` flag is True only when `error_count` is 0.
    Warnings and infos do not block the pipeline.
    """

    is_valid: bool = Field(
        ...,
        description="True if there are zero error-severity issues. Warnings/infos are allowed.",
    )
    total_issues: int = Field(
        ...,
        ge=0,
        description="Total number of issues found across all severities.",
    )
    error_count: int = Field(
        ...,
        ge=0,
        description="Number of error-severity issues.",
    )
    warning_count: int = Field(
        ...,
        ge=0,
        description="Number of warning-severity issues.",
    )
    info_count: int = Field(
        ...,
        ge=0,
        description="Number of info-severity issues.",
    )
    issues: list[ValidationIssue] = Field(
        default_factory=list,
        description="All validation issues found, ordered by severity (errors first).",
    )

    @model_validator(mode="after")
    def _check_counts(self) -> "ValidationReport":
        """Verify that severity counts match the issues list."""
        errors = sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)
        warnings = sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)
        infos = sum(1 for i in self.issues if i.severity == ValidationSeverity.INFO)

        if self.total_issues != len(self.issues):
            raise ValueError(
                f"total_issues ({self.total_issues}) != len(issues) ({len(self.issues)})"
            )
        if self.error_count != errors:
            raise ValueError(
                f"error_count ({self.error_count}) != actual errors ({errors})"
            )
        if self.warning_count != warnings:
            raise ValueError(
                f"warning_count ({self.warning_count}) != actual warnings ({warnings})"
            )
        if self.info_count != infos:
            raise ValueError(
                f"info_count ({self.info_count}) != actual infos ({infos})"
            )
        if self.is_valid and errors > 0:
            raise ValueError("is_valid cannot be True when error_count > 0")
        if not self.is_valid and errors == 0:
            raise ValueError("is_valid must be True when error_count == 0")

        return self

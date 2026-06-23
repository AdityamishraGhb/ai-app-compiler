"""
Stage 1 — Intent Extraction: Data Contracts

Converts a raw user prompt into a StructuredIntent that captures
the application's purpose, target users, features, and constraints.

Example JSON (StructuredIntent):
```json
{
    "app_name": "TaskFlow",
    "app_type": "web_application",
    "description": "A collaborative task management platform with deadline tracking and role-based access control for teams.",
    "target_users": ["admin", "team_lead", "team_member"],
    "core_features": [
        {
            "name": "task_management",
            "description": "Create, assign, update, and delete tasks with deadlines and priority levels",
            "priority": "critical"
        },
        {
            "name": "team_collaboration",
            "description": "Share tasks across teams, comment on tasks, and track team activity feeds",
            "priority": "high"
        },
        {
            "name": "role_based_access",
            "description": "Restrict feature access based on user roles (admin, lead, member)",
            "priority": "high"
        },
        {
            "name": "dashboard_analytics",
            "description": "Overview of task progress, team productivity, and deadline compliance",
            "priority": "medium"
        }
    ],
    "constraints": {
        "auth_required": true,
        "realtime": false,
        "file_uploads": false,
        "multi_tenancy": false,
        "i18n": false
    }
}
```
"""

from pydantic import Field

from backend.schemas.common import StrictBaseModel
from backend.schemas.enums import FeaturePriority


# ──────────────────────────────────────────────
#  Sub-models
# ──────────────────────────────────────────────

class CoreFeature(StrictBaseModel):
    """A single feature extracted from the user's requirements."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Machine-readable feature identifier (snake_case).",
        examples=["task_management", "user_auth"],
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Human-readable description of what this feature does.",
    )
    priority: FeaturePriority = Field(
        ...,
        description="Importance level of this feature to the application.",
    )


class AppConstraints(StrictBaseModel):
    """Non-functional constraints inferred from the user's prompt."""

    auth_required: bool = Field(
        True,
        description="Whether the application requires user authentication.",
    )
    realtime: bool = Field(
        False,
        description="Whether the application needs real-time features (WebSocket/SSE).",
    )
    file_uploads: bool = Field(
        False,
        description="Whether the application needs file upload capabilities.",
    )
    multi_tenancy: bool = Field(
        False,
        description="Whether the application serves multiple isolated tenants.",
    )
    i18n: bool = Field(
        False,
        description="Whether the application requires internationalization support.",
    )


# ──────────────────────────────────────────────
#  Stage 1 Output
# ──────────────────────────────────────────────

class StructuredIntent(StrictBaseModel):
    """
    **Stage 1 Output** — The structured representation of what the user wants to build.

    Produced by: `s1_intent/extractor.py`
    Consumed by: `s2_architecture/designer.py`
    """

    app_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="A concise, PascalCase name for the application (e.g., 'TaskFlow').",
        examples=["TaskFlow", "ShopHub", "DevBoard"],
    )
    app_type: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="The category of application being built. Reduce generic classifications (like 'web_application' or 'dashboard'). Prefer domain-specific app types (like 'music_management_system' or 'healthcare_erp') when confidence is high. Use snake_case.",
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="A clear, complete description of the application's purpose and scope.",
    )
    target_users: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "List of distinct user personas / roles that will use the application. "
            "Values should be snake_case identifiers (e.g., 'team_lead')."
        ),
        examples=[["admin", "team_lead", "team_member"]],
    )
    core_features: list[CoreFeature] = Field(
        ...,
        min_length=1,
        description="Features extracted from the user's requirements, ordered by priority.",
    )
    constraints: AppConstraints = Field(
        default_factory=AppConstraints,
        description="Non-functional requirements and platform constraints.",
    )

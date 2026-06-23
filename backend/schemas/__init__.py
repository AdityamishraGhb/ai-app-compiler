"""
Public API for backend.schemas — re-exports all data contracts.

Usage:
    from backend.schemas import (
        StructuredIntent,
        ArchitectureBlueprint,
        SchemaBundle,
        ValidationReport,
        RepairReport,
        RuntimeResult,
        PipelineRequest,
        PipelineResponse,
    )
"""

# ── Enums ────────────────────────────────────────────
from backend.schemas.enums import (  # noqa: F401
    APIParamType,
    AppType,
    AuthStrategy,
    CRUDOperation,
    FeaturePriority,
    FieldType,
    HTTPMethod,
    PageLayout,
    PipelineStatus,
    QueryStatus,
    RelationType,
    RepairActionType,
    RepairStrategy,
    ResponseType,
    SchemaLayerName,
    SQLiteColumnType,
    StageStatus,
    TableCreationStatus,
    UIComponentType,
    UIFieldType,
    ValidationCategory,
    ValidationSeverity,
)

# ── Common ───────────────────────────────────────────
from backend.schemas.common import StrictBaseModel  # noqa: F401

# ── Stage 1: Intent Extraction ──────────────────────
from backend.schemas.intent import (  # noqa: F401
    AppConstraints,
    CoreFeature,
    StructuredIntent,
)

# ── Stage 2: Architecture Design ────────────────────
from backend.schemas.architecture import (  # noqa: F401
    ArchitectureBlueprint,
    Entity,
    EntityAttribute,
    FeatureDefinition,
    FlowDefinition,
    PageDefinition,
    RoleDefinition,
)

# ── Stage 3: Schema Generation ──────────────────────
from backend.schemas.schema_bundle import (  # noqa: F401
    # UI
    UIComponent,
    UIFormField,
    UIPage,
    UISchema,
    UITableColumn,
    # API
    APIEndpoint,
    APIParam,
    APIRequestBody,
    APIResponse,
    APISchema,
    # Database
    DBColumn,
    DBIndex,
    DBTable,
    DatabaseSchema,
    ForeignKeyRef,
    # Auth
    AuthCredentials,
    AuthRole,
    AuthSchema,
    RouteGuard,
    # Bundle
    SchemaBundle,
)

# ── Stage 4: Validation ─────────────────────────────
from backend.schemas.validation import (  # noqa: F401
    IssueLocation,
    ValidationIssue,
    ValidationReport,
)

# ── Stage 5: Repair ─────────────────────────────────
from backend.schemas.repair import (  # noqa: F401
    RepairAction,
    RepairReport,
)

# ── Stage 6: Runtime Simulation ─────────────────────
from backend.schemas.runtime import (  # noqa: F401
    DatabaseInfo,
    RuntimeError_,
    RuntimeResult,
    SampleQueryResult,
    SeedDataResult,
    TableCreationResult,
)

# ── Pipeline ─────────────────────────────────────────
from backend.schemas.pipeline import (  # noqa: F401
    PipelineMetadata,
    PipelineOptions,
    PipelineRequest,
    PipelineResponse,
    StageResult,
)

__all__ = [
    # Enums
    "APIParamType",
    "AppType",
    "AuthStrategy",
    "CRUDOperation",
    "FeaturePriority",
    "FieldType",
    "HTTPMethod",
    "PageLayout",
    "PipelineStatus",
    "QueryStatus",
    "RelationType",
    "RepairActionType",
    "RepairStrategy",
    "ResponseType",
    "SchemaLayerName",
    "SQLiteColumnType",
    "StageStatus",
    "TableCreationStatus",
    "UIComponentType",
    "UIFieldType",
    "ValidationCategory",
    "ValidationSeverity",
    # Common
    "StrictBaseModel",
    # Stage 1
    "AppConstraints",
    "CoreFeature",
    "StructuredIntent",
    # Stage 2
    "ArchitectureBlueprint",
    "Entity",
    "EntityAttribute",
    "FeatureDefinition",
    "FlowDefinition",
    "PageDefinition",
    "RoleDefinition",
    # Stage 3 — UI
    "UIComponent",
    "UIFormField",
    "UIPage",
    "UISchema",
    "UITableColumn",
    # Stage 3 — API
    "APIEndpoint",
    "APIParam",
    "APIRequestBody",
    "APIResponse",
    "APISchema",
    # Stage 3 — Database
    "DBColumn",
    "DBIndex",
    "DBTable",
    "DatabaseSchema",
    "ForeignKeyRef",
    # Stage 3 — Auth
    "AuthCredentials",
    "AuthRole",
    "AuthSchema",
    "RouteGuard",
    # Stage 3 — Bundle
    "SchemaBundle",
    # Stage 4
    "IssueLocation",
    "ValidationIssue",
    "ValidationReport",
    # Stage 5
    "RepairAction",
    "RepairReport",
    # Stage 6
    "DatabaseInfo",
    "RuntimeError_",
    "RuntimeResult",
    "SampleQueryResult",
    "SeedDataResult",
    "TableCreationResult",
    # Pipeline
    "PipelineMetadata",
    "PipelineOptions",
    "PipelineRequest",
    "PipelineResponse",
    "StageResult",
]

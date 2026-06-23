"""
Enumeration types for the AI Application Compiler pipeline.

Every categorical field across all 14 data contracts is backed by an enum
defined here, ensuring type safety, IDE autocompletion, and deterministic
validation at every pipeline stage.
"""

from enum import Enum


# ──────────────────────────────────────────────
#  Stage 1 — Intent Extraction
# ──────────────────────────────────────────────


class FeaturePriority(str, Enum):
    """Priority level for a requested feature."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ──────────────────────────────────────────────
#  Stage 2 — Architecture Design
# ──────────────────────────────────────────────

class FieldType(str, Enum):
    """Logical data type for entity attributes (database-agnostic)."""
    UUID = "uuid"
    STRING = "string"
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    JSON = "json"
    ENUM = "enum"
    EMAIL = "email"
    URL = "url"
    PASSWORD = "password"


class CRUDOperation(str, Enum):
    """Standard CRUD operation type."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class RelationType(str, Enum):
    """Cardinality of an entity relationship."""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"


# ──────────────────────────────────────────────
#  Stage 3 — Schema Generation (UI)
# ──────────────────────────────────────────────

class PageLayout(str, Enum):
    """Layout template for a UI page."""
    SIDEBAR = "sidebar"
    TOP_NAV = "top_nav"
    FULL_WIDTH = "full_width"
    SPLIT = "split"
    DASHBOARD_GRID = "dashboard_grid"
    CENTERED = "centered"


class UIComponentType(str, Enum):
    """Type of a UI component rendered on a page."""
    DATA_TABLE = "data_table"
    FORM = "form"
    MODAL_FORM = "modal_form"
    CARD_GRID = "card_grid"
    DETAIL_VIEW = "detail_view"
    CHART = "chart"
    STATS_BAR = "stats_bar"
    NAVIGATION = "navigation"
    CALENDAR = "calendar"
    KANBAN_BOARD = "kanban_board"
    LIST_VIEW = "list_view"
    HERO_SECTION = "hero_section"


class UIFieldType(str, Enum):
    """Input field type within a UI form component."""
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    EMAIL = "email"
    PASSWORD = "password"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DATE = "date"
    DATETIME = "datetime"
    FILE = "file"
    ENTITY_SELECT = "entity_select"
    TOGGLE = "toggle"
    COLOR = "color"
    RICH_TEXT = "rich_text"


# ──────────────────────────────────────────────
#  Stage 3 — Schema Generation (API)
# ──────────────────────────────────────────────

class HTTPMethod(str, Enum):
    """HTTP method for an API endpoint."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class APIParamType(str, Enum):
    """Data type for API query/path parameters."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    UUID = "uuid"


class ResponseType(str, Enum):
    """Shape of an API response payload."""
    SINGLE = "single"
    LIST = "list"
    PAGINATED_LIST = "paginated_list"
    EMPTY = "empty"


# ──────────────────────────────────────────────
#  Stage 3 — Schema Generation (Database)
# ──────────────────────────────────────────────

class SQLiteColumnType(str, Enum):
    """SQLite column affinity types."""
    TEXT = "TEXT"
    INTEGER = "INTEGER"
    REAL = "REAL"
    BLOB = "BLOB"
    NUMERIC = "NUMERIC"


# ──────────────────────────────────────────────
#  Stage 3 — Schema Generation (Auth)
# ──────────────────────────────────────────────

class AuthStrategy(str, Enum):
    """Authentication strategy for the generated application."""
    JWT = "jwt"
    SESSION = "session"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"


# ──────────────────────────────────────────────
#  Stage 4 — Validation
# ──────────────────────────────────────────────

class ValidationSeverity(str, Enum):
    """Severity level of a validation issue."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationCategory(str, Enum):
    """Category of a validation check."""
    STRUCTURAL = "structural"
    REFERENTIAL = "referential"
    LOGICAL = "logical"


# ──────────────────────────────────────────────
#  Stage 5 — Repair
# ──────────────────────────────────────────────

class RepairActionType(str, Enum):
    """Type of repair action applied to fix a validation issue."""
    ADDED_FIELD = "added_field"
    REMOVED_FIELD = "removed_field"
    MODIFIED_FIELD = "modified_field"
    ADDED_REFERENCE = "added_reference"
    REMOVED_REFERENCE = "removed_reference"
    ADDED_ENDPOINT = "added_endpoint"
    REMOVED_ENDPOINT = "removed_endpoint"
    ADDED_COLUMN = "added_column"
    REMOVED_COLUMN = "removed_column"
    MODIFIED_CONSTRAINT = "modified_constraint"
    ADDED_INDEX = "added_index"
    ADDED_INCLUDE = "added_include"
    ADDED_ROUTE_GUARD = "added_route_guard"
    SCHEMA_RESTRUCTURED = "schema_restructured"


class RepairStrategy(str, Enum):
    """Strategy used to perform a repair."""
    DETERMINISTIC = "deterministic"
    LLM_ASSISTED = "llm_assisted"


# ──────────────────────────────────────────────
#  Stage 6 — Runtime Simulation
# ──────────────────────────────────────────────

class TableCreationStatus(str, Enum):
    """Result of attempting to create a SQLite table."""
    CREATED = "created"
    FAILED = "failed"
    SKIPPED = "skipped"


class QueryStatus(str, Enum):
    """Result of executing a sample SQL query."""
    PASSED = "passed"
    FAILED = "failed"


# ──────────────────────────────────────────────
#  Pipeline-level
# ──────────────────────────────────────────────

class PipelineStatus(str, Enum):
    """Overall result of the full compilation pipeline."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class StageStatus(str, Enum):
    """Execution status of a single pipeline stage."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"


class SchemaLayerName(str, Enum):
    """Identifier for a schema layer within the SchemaBundle."""
    UI = "ui"
    API = "api"
    DATABASE = "database"
    AUTH = "auth"

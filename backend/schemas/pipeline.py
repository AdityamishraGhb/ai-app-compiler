"""
Pipeline-level Data Contracts: Request, Response, and Stage Metadata.

These are the top-level API models — the PipelineRequest is the input to
POST /compile, and PipelineResponse is the output.

Example JSON (PipelineRequest):
```json
{
    "prompt": "Build a task management app with team collaboration, deadlines, and role-based access",
    "options": {
        "max_repair_iterations": 3,
        "include_seed_data": true,
        "target_database": "sqlite",
        "run_simulation": true,
        "verbose": false
    }
}
```

Example JSON (PipelineResponse):
```json
{
    "pipeline_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "success",
    "stages": {
        "s1_intent": {
            "name": "s1_intent",
            "status": "success",
            "duration_ms": 1200,
            "output": { "...StructuredIntent..." },
            "error": null
        },
        "s2_architecture": {
            "name": "s2_architecture",
            "status": "success",
            "duration_ms": 2100,
            "output": { "...ArchitectureBlueprint..." },
            "error": null
        },
        "s3_schema": {
            "name": "s3_schema",
            "status": "success",
            "duration_ms": 3400,
            "output": { "...SchemaBundle..." },
            "error": null
        },
        "s4_validation": {
            "name": "s4_validation",
            "status": "success",
            "duration_ms": 50,
            "output": { "...ValidationReport..." },
            "error": null
        },
        "s5_repair": {
            "name": "s5_repair",
            "status": "skipped",
            "duration_ms": 0,
            "output": null,
            "error": null
        },
        "s6_runtime": {
            "name": "s6_runtime",
            "status": "success",
            "duration_ms": 120,
            "output": { "...RuntimeResult..." },
            "error": null
        }
    },
    "final_config": {
        "ui": { "...UISchema..." },
        "api": { "...APISchema..." },
        "database": { "...DatabaseSchema..." },
        "auth": { "...AuthSchema..." }
    },
    "metadata": {
        "total_duration_ms": 6870,
        "llm_calls_made": 6,
        "repair_iterations_used": 0,
        "input_prompt_length": 85,
        "output_token_estimate": 4200,
        "timestamp_utc": "2026-06-24T02:35:00Z"
    }
}
```
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from backend.schemas.common import StrictBaseModel
from backend.schemas.enums import PipelineStatus, StageStatus


# ──────────────────────────────────────────────
#  Pipeline Options
# ──────────────────────────────────────────────

class PipelineOptions(StrictBaseModel):
    """Configuration options for a pipeline run."""

    max_repair_iterations: int = Field(
        3,
        ge=0,
        le=10,
        description=(
            "Maximum number of validation→repair loop iterations. "
            "0 means no repair; validation failures halt the pipeline."
        ),
    )
    include_seed_data: bool = Field(
        True,
        description="Whether to generate and insert seed data during runtime simulation.",
    )
    target_database: str = Field(
        "sqlite",
        description="Target database dialect. Currently only 'sqlite' is supported.",
    )
    run_simulation: bool = Field(
        True,
        description="Whether to execute Stage 6 (runtime simulation).",
    )
    verbose: bool = Field(
        False,
        description="If True, include extra debugging metadata in the response.",
    )


# ──────────────────────────────────────────────
#  Pipeline Request (POST /compile input)
# ──────────────────────────────────────────────

class PipelineRequest(StrictBaseModel):
    """
    **API Input** — The request body for POST /compile.

    Contains the user's natural language prompt and optional
    configuration for the compilation pipeline.
    """

    prompt: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description=(
            "Natural language description of the application to build. "
            "Should describe features, user roles, and key requirements."
        ),
        examples=[
            "Build a task management app with team collaboration, deadlines, and role-based access",
            "Create an e-commerce platform with product catalog, shopping cart, and payment integration",
        ],
    )
    options: PipelineOptions = Field(
        default_factory=PipelineOptions,
        description="Pipeline configuration options.",
    )


# ──────────────────────────────────────────────
#  Stage Result (per-stage metadata in response)
# ──────────────────────────────────────────────

class StageResult(StrictBaseModel):
    """Execution metadata and output for a single pipeline stage."""

    name: str = Field(
        ...,
        min_length=1,
        description="Stage identifier (e.g., 's1_intent', 's4_validation').",
        examples=["s1_intent", "s2_architecture", "s3_schema", "s4_validation", "s5_repair", "s6_runtime"],
    )
    status: StageStatus = Field(
        ...,
        description="Execution status of this stage.",
    )
    duration_ms: int = Field(
        0,
        ge=0,
        description="Wall-clock execution time in milliseconds.",
    )
    output: dict[str, Any] | None = Field(
        None,
        description=(
            "Serialized output of the stage (dict form of the Pydantic model). "
            "None if the stage was skipped or failed before producing output."
        ),
    )
    error: str | None = Field(
        None,
        description="Error message if the stage failed.",
    )


# ──────────────────────────────────────────────
#  Pipeline Metadata
# ──────────────────────────────────────────────

class PipelineMetadata(StrictBaseModel):
    """Aggregate metrics for the full pipeline run."""

    total_duration_ms: int = Field(
        ...,
        ge=0,
        description="Total wall-clock time for all stages in milliseconds.",
    )
    llm_calls_made: int = Field(
        ...,
        ge=0,
        description="Total number of LLM API calls made across all stages.",
    )
    repair_iterations_used: int = Field(
        ...,
        ge=0,
        description="Number of validation→repair loop iterations executed.",
    )
    input_prompt_length: int = Field(
        ...,
        ge=0,
        description="Character length of the input prompt.",
    )
    output_token_estimate: int = Field(
        0,
        ge=0,
        description="Estimated total output tokens across all LLM calls.",
    )
    timestamp_utc: datetime = Field(
        ...,
        description="UTC timestamp when the pipeline completed.",
    )


# ──────────────────────────────────────────────
#  Pipeline Response (POST /compile output)
# ──────────────────────────────────────────────

class PipelineResponse(StrictBaseModel):
    """
    **API Output** — The response body for POST /compile.

    Contains per-stage results, the final validated configuration
    (SchemaBundle as dict), and aggregate metadata.

    `final_config` is only populated when `status` is 'success' or 'partial'.
    On 'failed', it is None and the caller should inspect `stages` for errors.
    """

    pipeline_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for this pipeline run (UUID v4).",
    )
    status: PipelineStatus = Field(
        ...,
        description=(
            "'success' = all stages passed; "
            "'partial' = completed with unresolved warnings; "
            "'failed' = a stage produced errors that could not be repaired."
        ),
    )
    stages: dict[str, StageResult] = Field(
        ...,
        description=(
            "Per-stage results keyed by stage name "
            "('s1_intent', 's2_architecture', 's3_schema', 's4_validation', 's5_repair', 's6_runtime')."
        ),
    )
    final_config: dict[str, Any] | None = Field(
        None,
        description=(
            "The final SchemaBundle (serialized as dict) after all stages complete. "
            "None on pipeline failure."
        ),
    )
    metadata: PipelineMetadata = Field(
        ...,
        description="Aggregate metrics for the pipeline run.",
    )

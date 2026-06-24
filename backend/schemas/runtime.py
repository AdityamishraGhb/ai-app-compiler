from typing import List

from backend.schemas.common import StrictBaseModel
from pydantic import Field

class RuntimeResult(StrictBaseModel):
    """
    Result of the Stage 6 Runtime Simulation.
    """
    success: bool = Field(
        ...,
        description="True if all statements executed successfully.",
    )
    tables_created: List[str] = Field(
        default_factory=list,
        description="List of table names that were successfully created.",
    )
    statements_executed: List[str] = Field(
        default_factory=list,
        description="List of all SQL statements executed.",
    )
    execution_errors: List[str] = Field(
        default_factory=list,
        description="List of error messages encountered during execution.",
    )

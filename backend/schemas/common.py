"""
Shared base configuration and utility types used across all data contracts.

Provides:
- A common Pydantic BaseModel config for all pipeline models
- Shared sub-models that appear in multiple stage contracts
"""

from pydantic import BaseModel, ConfigDict


class StrictBaseModel(BaseModel):
    """
    Base model for all pipeline data contracts.

    Configuration:
    - `populate_by_name=True`:  Accept both alias and field name in JSON input.
    - `use_enum_values=True`:   Serialize enums to their string values.
    - `validate_assignment=True`: Re-validate on field assignment.
    - `extra="forbid"`:          Reject unexpected fields for strict contracts.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        validate_assignment=True,
        extra="forbid",
        ser_json_inf_nan="constants",
    )

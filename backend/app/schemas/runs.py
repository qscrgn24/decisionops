from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class RunConfig(BaseModel):
    # Core constraints
    budget: float = Field(..., gt=0)
    max_items: int | None = Field(default=None, gt=0)

    # Optional knobs (for later use)
    lambda_risk: float = Field(default=0.0, ge=0.0) # weight for risk in optimization
    objective: Literal["value", "risk_adjusted_value"] = "value"


class RunCreate(BaseModel):
    dataset_id: str
    config: RunConfig


class RunOut(BaseModel):
    id: str
    dataset_id: str
    status: str

    config_json: dict[str, Any] | None
    result_json: dict[str, Any] | None
    error: str | None

    created_at: datetime
    updated_at: datetime
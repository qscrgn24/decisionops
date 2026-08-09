from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings


class RunConfig(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    # Core constraints
    budget: float = Field(..., gt=0, le=settings.MAX_NUMERIC_VALUE)
    max_items: int | None = Field(default=None, gt=0, le=settings.MAX_MAX_ITEMS)

    # Optional knobs (for later use)
    lambda_risk: float = Field(default=0.0, ge=0.0, le=settings.MAX_NUMERIC_VALUE) # weight for risk in optimization
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
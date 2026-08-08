from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings

Objective = Literal["value", "risk_adjusted_value"]


class ExecuteAllIn(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    dataset_id: str
    budget: float = Field(..., gt=0, le=settings.MAX_NUMERIC_VALUE)
    max_items: int | None = Field(None, gt=0, le=settings.MAX_MAX_ITEMS)
    lambda_risk: float = Field(0.0, ge=0.0, le=settings.MAX_NUMERIC_VALUE)
    objective: Objective = "risk_adjusted_value"

    # optional solver controls
    time_limit_s: float = Field(default=settings.DEFAULT_SOLVER_TIME_S, ge=0.1, le=settings.MAX_SOLVER_TIME_S)
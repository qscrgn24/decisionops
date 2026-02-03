from pydantic import BaseModel, Field
from typing import Literal

Objective = Literal["value", "risk_adjusted_value"]

class ExecuteAllIn(BaseModel):
    dataset_id: str
    budget: float = Field(..., gt=0)
    max_items: int | None = Field(None, gt=0)
    lambda_risk: float = Field(0.0, ge=0.0)
    objective: Objective = "risk_adjusted_value"

    # optional solver controls
    time_limit_s: float = Field(5.0, ge=0.1, le=60.0)
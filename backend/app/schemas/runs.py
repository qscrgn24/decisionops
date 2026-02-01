from datetime import datetime
from pydantic import BaseModel


class RunCreate(BaseModel):
    dataset_id: str


class RunOut(BaseModel):
    id: str
    dataset_id: str
    status: str
    created_at: datetime
from datetime import datetime

from pydantic import BaseModel


class DatasetOut(BaseModel):
    id: str
    name: str
    original_filename: str
    created_at: datetime
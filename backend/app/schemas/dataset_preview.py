from typing import Any
from pydantic import BaseModel


class DatasetPreviewOut(BaseModel):
    dataset_id: str
    columns: list[str]
    total_rows: int

    has_category: bool
    has_risk: bool
    risk_scale: str | None  # "0-1" | "0-100 | None

    # New: column resolution metadata (for forgiving UX)
    resolved_columns: dict[str, str | None] = {}   # canon -> original column name (or None)
    missing_required: list[str] = []               # e.g. ["cost","value"] if not resolved


    rows: list[dict[str, Any]]  # preview rows
    warnings: list[str]
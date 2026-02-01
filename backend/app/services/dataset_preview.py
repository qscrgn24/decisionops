import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_COLS = {"item_id", "name", "cost", "value"}
OPTIONAL_COLS = {"category", "risk"}

@dataclass
class PreviewResult:
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int
    has_category: bool
    has_risk: bool
    risk_scale: str | None # "0-1" | "0-100" | None
    warnings : list[str]


def _parse_float(value, field, row_idx):
    try:
        return float(value)
    except Exception:
        raise ValueError(f"Row {row_idx}: Invalid number for '{field}': {value!r}")
    

def preview_and_validate_csv(file_path, *, n: int = 20):
    if n < 1:
        n = 1
    if n > 200:
        n = 200   # prevent huge responnses

    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    warnings = []

    # --- Pass 1: read header + detect columns + compute max risk + count rows ---
    total_rows = 0
    max_risk = None # type: float | None
    has_category = False
    has_risk = False

    with file_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV file is missing a header row.")
        
        columns = [c.strip() for c in reader.fieldnames if c is not None]
        columns_set = set(columns)

        missing = sorted(REQUIRED_COLS - columns_set)
        if missing:
            raise ValueError(f"Missing required columns: {missing}. Required {sorted(REQUIRED_COLS)}")

        has_category = "category" in columns_set
        has_risk = "risk" in columns_set

        for row in reader:
            total_rows += 1
            if has_risk:
                risk_raw = row.get("risk", "").strip()
                if risk_raw == "":
                    continue
                risk_value = _parse_float(risk_raw, "risk", total_rows)
                if max_risk is None or risk_value > max_risk:
                    max_risk = risk_value

    if total_rows == 0:
        raise ValueError("CSV file contains no data rows.")
        
    risk_scale = None
    if has_risk:
        if max_risk is None:
            warnings.append("Risk column exists but all risk values are empty; treating risk as 0.")
            risk_scale = "0-1"
        elif max_risk <= 1.0:
            risk_scale = "0-1"
        elif max_risk <= 100.0:
            risk_scale = "0-100"
            warnings.append("Risk detected in [0,100]; normalizing to [0,1].")
        else:
            raise ValueError("Risk values must be in [0,1] or [0,100].")
            
    # --- Pass 2: produce preview rows (first n) with basic type validation ---
    rows_out = []

    with file_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row_idx, row in enumerate(reader, start=1):
            if row_idx > n:
                break

            item_id = (row.get("item_id") or "").strip()
            name = (row.get("name") or "").strip()
            cost_raw = (row.get("cost") or "").strip()
            value_raw = (row.get("value") or "").strip()

            if item_id == "":
                raise ValueError(f"Row {row_idx}: 'item_id' cannot be empty.")
            if name == "":
                raise ValueError(f"Row {row_idx}: 'name' cannot be empty.")
            
            cost = _parse_float(cost_raw, "cost", row_idx)
            value = _parse_float(value_raw, "value", row_idx)

            if cost < 0:
                raise ValueError(f"Row {row_idx}: 'cost' cannot be negative.")
            if value < 0:
                raise ValueError(f"Row {row_idx}: 'value' cannot be negative.")
            
            row_out = {
                "item_id": item_id,
                "name": name,
                "cost": cost,
                "value": value,
            }

            if has_category:
                row_out["category"] = (row.get("category") or "").strip()

            if has_risk:
                risk_raw = (row.get("risk") or "").strip()
                if risk_raw == "":
                    risk_value = 0.0
                    warnings.append("Some rows have empty risk; treating missing risk as 0.")
                else:
                    risk_value = _parse_float(risk_raw, "risk", row_idx)
                    if risk_scale == "0-100":
                        risk_value = risk_value / 100.0
                row_out["risk"] = risk_value


            rows_out.append(row_out)

    # Deduplication warnings (keep order)
    deduped = []
    seen = set()
    for w in warnings:
        if w not in seen:
            deduped.append(w)
            seen.add(w)

    return PreviewResult(
        columns=columns,
        rows=rows_out,
        total_rows=total_rows,
        has_category=has_category,
        has_risk=has_risk,
        risk_scale=risk_scale,
        warnings=deduped
    )


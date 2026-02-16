import csv
import io
from dataclasses import dataclass
from typing import Any

from app.services.csv_normalize import resolve_columns
from app.services.parse_numbers import parse_float

@dataclass
class PreviewResult:
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int
    has_category: bool
    has_risk: bool
    risk_scale: str | None # "0-1" | "0-100" | None
    warnings : list[str]

    # New: forgiving UX metadata
    resolved_columns: dict[str, str | None]  # canon -> original column name (or None)
    missing_required: list[str]


def _dedupe(warnings: list[str]):
    # Deduplication warnings (keep order)
    deduped = []
    seen = set()
    for w in warnings:
        if w not in seen:
            deduped.append(w)
            seen.add(w)
    return deduped


def _open_csv_text_stream(file_bytes: bytes) -> io.StringIO:
    """
    Convert raw bytes (from DB) into a text stream for csv.DictReader.
    We default to utf-8, and fall back to utf-8-sig to handle BOM.
    """
    if not isinstance(file_bytes, (bytes, bytearray)):
        raise TypeError("preview_and_validate_csv expected raw CSV bytes.")

    if len(file_bytes) == 0:
        raise ValueError("Uploaded file is empty.")

    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        # Common BOM / encoding edge cases; utf-8-sig can help with BOM
        text = file_bytes.decode("utf-8-sig", errors="replace")

    return io.StringIO(text)


def preview_and_validate_csv(file_bytes: bytes, *, n: int = 20):
    if n < 1:
        n = 1
    if n > 200:
        n = 200   # prevent huge responnses
    
    warnings: list[str] = []

    # --- Pass 1: read header + detect columns + compute max risk + count rows ---
    total_rows = 0
    max_risk = None # type: float | None

    f1 = _open_csv_text_stream(file_bytes)
    reader = csv.DictReader(f1)
    if reader.fieldnames is None:
        raise ValueError("CSV file is missing a header row.")
    
    # IMPORTANT:
    # - Use RAW headers for resolve_columns so row.get(col) matches DictReader keys exactly.
    # - Keep a stripped version only for display back to the frontend.
    raw_columns = [c for c in reader.fieldnames if c is not None]
    columns = [c.strip() for c in raw_columns]
    res = resolve_columns(raw_columns)

    # canon -> original column name (or None)
    resolved_columns = {k: res.mapping.get(k) for k in ["item_id", "name", "cost", "value", "category", "risk"]}

    has_category = resolved_columns["category"] is not None
    has_risk = resolved_columns["risk"] is not None

    risk_col = resolved_columns["risk"]

    for row in reader:
        total_rows += 1
        if has_risk and risk_col:
            risk_raw = (row.get(risk_col) or "").strip()
            if risk_raw == "":
                continue
            risk_value = parse_float(risk_raw, default=None)
            if risk_value is None:
                # Don't hard-fail preview; warn and ignore for scale detection
                warnings.append(f"Some rows have non-numeric risk values; treating missing/invalid risk as 0.")
                continue
            if max_risk is None or risk_value > max_risk:
                max_risk = risk_value

    if total_rows == 0:
        return PreviewResult(
            columns=columns,
            rows = [],
            total_rows=0,
            has_category=False,
            has_risk=False,
            risk_scale=None,
            warnings=["CSV file contains no data rows."],
            resolved_columns=resolved_columns,
            missing_required=res.missing_required,
        )

    # If required columns missing, be forgiving: return metadata + warnings + empty rows
    if res.missing_required:
        warnings = list(res.warnings) + warnings
        warnings.append(f"Missing required columns (after aliasing): {res.missing_required}.")
        return PreviewResult(
            columns=columns,
            rows=[],
            total_rows=total_rows,
            has_category=has_category,
            has_risk=has_risk,
            risk_scale=None,
            warnings=_dedupe(warnings),
            resolved_columns=resolved_columns,
            missing_required=res.missing_required,
        )
        
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
            warnings.append("Risk values must be in [0,1] or [0,100]. Treating invalid risk as 0.")
            risk_scale = "0-1"
            
    # --- Pass 2: produce preview rows (first n) with basic type validation ---
    rows_out: list[dict[str, Any]] = []

    col_item_id = resolved_columns["item_id"]
    col_name = resolved_columns["name"]
    col_cost = resolved_columns["cost"]
    col_value = resolved_columns["value"]
    col_category = resolved_columns["category"]
    col_risk = resolved_columns["risk"]

    f2 = _open_csv_text_stream(file_bytes)
    reader = csv.DictReader(f2)

    for row_idx, row in enumerate(reader, start=1):
        if row_idx > n:
            break

        name = (row.get(col_name) or "").strip() if col_name else ""
        if name == "":
            # skip empty rows
            continue

        cost_raw = (row.get(col_cost) or "").strip() if col_cost else ""
        value_raw = (row.get(col_value) or "").strip() if col_value else ""

        cost = parse_float(cost_raw, default=None)
        value = parse_float(value_raw, default=None)

        if cost is None or value is None:
            warnings.append("Some rows have invalid cost/value; preview may be incomplete.")
            continue

        if cost < 0:
            warnings.append("Some rows have negative cost; preview may be incomplete.")
            continue
        if value < 0:
            warnings.append("Some rows have negative value; preview may be incomplete.")
            continue

        # item_id is optional; auto-generate if absent or empty
        item_id = ""
        if col_item_id:
            item_id = (row.get(col_item_id) or "").strip()
        if item_id == "":
            item_id = f"I{row_idx}"

        row_out: dict[str, Any] = {
            (k.strip() if k is not None else ""): (v.strip() if isinstance(v, str) else v)
            for k, v in row.items()
            if k is not None and k.strip() != ""
        }

        if col_item_id:
            row_out[col_item_id.strip()] = item_id
        else:
            row_out["item_id"] = item_id

        if col_name:
            row_out[col_name.strip()] = name

        if col_cost:
            row_out[col_cost.strip()] = float(cost)

        if col_value:
            row_out[col_value.strip()] = float(value)

        if has_category and col_category:
            row_out[col_category.strip()] = (row.get(col_category) or "").strip()

        if has_risk and col_risk:
            risk_raw = (row.get(col_risk) or "").strip()
            rv = parse_float(risk_raw, default=0.0)
            if rv is None:
                rv = 0.0
            if risk_scale == "0-100":
                rv = rv / 100.0
            row_out[col_risk.strip()] = float(rv)

        rows_out.append(row_out)

    warnings = list(res.warnings) + warnings

    return PreviewResult(
        columns=columns,
        rows=rows_out,
        total_rows=total_rows,
        has_category=has_category,
        has_risk=has_risk,
        risk_scale=risk_scale,
        warnings=_dedupe(warnings),
        resolved_columns=resolved_columns,
        missing_required=[],
    )

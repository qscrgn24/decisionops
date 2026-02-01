import csv
from pathlib import Path
from typing import Any

from app.services.dataset_preview import REQUIRED_COLS, _parse_float # reuse existing helpers


def _detect_risk_scale(file_path: Path):
    """Return '0-1', '0-100', or None if no risk column."""
    max_risk = None

    with file_path.open("r", newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV file has no header row.")
        
        columns = [c.strip() for c in reader.fieldnames if c is not None]
        columns_set = set(columns)

        missing = sorted(REQUIRED_COLS - columns_set)
        if missing:
            raise ValueError(f"Missing required columns: {missing}. Required {sorted(REQUIRED_COLS)}")
        
        if "risk" not in columns_set:
            return None

        row_idx = 0
        for row in reader:
            row_idx += 1
            risk_raw = row.get("risk", "").strip()
            if risk_raw == "":
                continue
            risk_value = _parse_float(risk_raw, "risk", row_idx)
            if max_risk is None or risk_value > max_risk:
                max_risk = risk_value
        
    if max_risk is None:
        return '0-1' # treat as 0 if empty
    if max_risk >= 0.0 and max_risk <= 1.0:
        return '0-1'
    if max_risk >= 0.0 and max_risk <= 100.0:
        return '0-100'
    
    raise ValueError("Risk values must be in [0,1] or [0,100].")


def _iter_items(file_path: Path):
    """
    Returns (columns, items, risk_scale).
    Each item contains: item_id, name, cost, value, category(optional), risk(optional normalized 0-1)
    """
    risk_scale = _detect_risk_scale(file_path)

    with file_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        columns = [c.strip() for c in reader.fieldnames if c is not None]
        columns_set = set(columns)

        has_category = "category" in columns_set
        has_risk = "risk" in columns_set

        items: list[dict[str, Any]] = []
        row_idx = 0
        for row in reader:
            row_idx += 1
            item_id = (row.get("item_id") or "").strip()
            name = (row.get("name") or "").strip()

            if item_id == "":
                raise ValueError(f"Row {row_idx}: item_id is empty")
            if name == "":
                raise ValueError(f"Row {row_idx}: name is empty")
            
            cost = _parse_float((row.get("cost") or "").strip(), "cost", row_idx)
            value = _parse_float((row.get("value") or "").strip(), "value", row_idx)

            if cost <= 0:
                raise ValueError(f"Row {row_idx}: cost must be > 0")
            if value <= 0:
                raise ValueError(f"Row {row_idx}: value must be >= 0")
            
            item: dict[str, Any] = {
                "item_id": item_id,
                "name": name,
                "cost": cost,
                "value": value,
            }

            if has_category:
                item["category"] = (row.get("category") or "").strip() or None

            if has_risk:
                risk_raw = (row.get("risk") or "").strip()
                if risk_raw == "":
                    risk_value = 0.0
                else:
                    risk_value = _parse_float(risk_raw, "risk", row_idx)
                    if risk_scale == '0-100':
                        risk_value /= 100.0
                item["risk"] = risk_value
            
            items.append(item)

    if len(items) == 0:
        raise ValueError("CSV has no data rows")
    
    return columns, items, risk_scale


def greedy_select(*, file_path: Path, budget: float, max_items: int | None, objective: str, lambda_risk: float):
    """
    Greedy baseline:
      - Score per cost descending
      - Add while budget allows
      - Optional max_items cap
    """
    
    columns, items, risk_scale = _iter_items(file_path)

    has_risk = any("risk" in it for it in items)

    def item_score(item: dict[str, Any]):
        value = float(item["value"])
        cost = float(item["cost"])
        risk = float(item.get("risk", 0.0))
        if objective == "risk_adjusted_value":
            value_eff = value - lambda_risk * risk
        else:
            value_eff = value
        return value_eff / cost
    
    # Sort by score desc (stable tie-breakers for determinism)
    items_sorted = sorted(items, key=lambda item: (item_score(item), float(item["value"]), -float(item["cost"])), reverse=True)

    selected: list[dict[str, Any]] = []
    total_cost = 0.0
    total_value = 0.0
    total_risk = 0.0

    cap = max_items if max_items is not None else 10 ** 9

    for item in items_sorted:
        if len(selected) >= cap:
            break

        cur_cost = float(item["cost"])
        if total_cost + cur_cost <= budget + 1e-9:
            selected.append(item)
            total_cost += cur_cost
            total_value += float(item["value"])
            if has_risk:
                total_risk += float(item.get("risk", 0.0))

    result = {
        "mathod": "greedy_v1",
        "objective": objective,
        "lambda_risk": lambda_risk,
        "budget": budget,
        "max_items": max_items,
        "risk_scale": risk_scale,
        "summary": {
            "selected_count": len(selected),
            "total_cost": total_cost,
            "total_value": total_value,
            "total_risk": total_risk if has_risk else None,
        },
        "selected_items": [
            {
                "item_id": item["item_id"],
                "name": item["name"],
                "cost": item["cost"],
                "value": item["value"],
                "risk": item.get("risk", None),
                "category": item.get("category", None),
            }
            for item in selected
        ],
        "columns": columns,
    }

    return result
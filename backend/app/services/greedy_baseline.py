from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Tuple

from app.services.csv_normalize import resolve_columns
from app.services.parse_numbers import parse_float


def _iter_items(file_path: Path) -> Tuple[list[str], list[dict[str, Any]], float]:
    """
    Loads CSV and returns:
      - columns: original CSV columns
      - items: canonicalized dicts with keys: item_id, name, cost, value, category?, risk?
      - risk_scale: 1.0 or 100.0 (used if original looked like percentages)
    """
    with open(file_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        res = resolve_columns(columns)

        # Require that name/cost/value can be resolved (via aliases)
        if res.missing_required:
            raise ValueError(f"Missing required columns (after aliasing): {res.missing_required}")

        col_item_id = res.mapping.get("item_id")  # optional
        col_name = res.mapping["name"]
        col_cost = res.mapping["cost"]
        col_value = res.mapping["value"]
        col_category = res.mapping.get("category")
        col_risk = res.mapping.get("risk")

        raw_items: list[dict[str, Any]] = []
        risks_raw: list[float] = []

        for idx, row in enumerate(reader, start=1):
            name = (row.get(col_name) or "").strip()
            if not name:
                # skip empty rows
                continue

            cost = parse_float(row.get(col_cost), default=None)
            value = parse_float(row.get(col_value), default=None)

            if cost is None or value is None:
                raise ValueError(f"Row {idx}: cost/value not parseable")

            if cost <= 0:
                raise ValueError(f"Row {idx}: cost must be > 0")

            item_id = (row.get(col_item_id) or "").strip() if col_item_id else ""
            if not item_id:
                item_id = f"I{idx}"

            item: dict[str, Any] = {
                "item_id": item_id,
                "name": name,
                "cost": float(cost),
                "value": float(value),
            }

            if col_category:
                cat = (row.get(col_category) or "").strip()
                if cat:
                    item["category"] = cat

            if col_risk:
                r = parse_float(row.get(col_risk), default=None)
                if r is not None:
                    item["risk"] = float(r)
                    risks_raw.append(float(r))

            raw_items.append(item)

    # Risk normalization: if it looks like 0..100, map to 0..1
    risk_scale = 1.0
    if risks_raw:
        mx = max(risks_raw)
        if mx > 1.0 and mx <= 100.0:
            risk_scale = 100.0
            for it in raw_items:
                if "risk" in it:
                    it["risk"] = float(it["risk"]) / 100.0

    return columns, raw_items, risk_scale


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
from __future__ import annotations

import math
from typing import Any

from ortools.sat.python import cp_model

from app.core.config import settings
from app.services.greedy_baseline import _iter_items


def _scale_to_int(value: float, scale: int) -> int:
    return int(round(value * scale))


def _validate_solver_time_limit(time_limit_s: float) -> float:
    time_limit = float(time_limit_s)

    if not math.isfinite(time_limit):
        raise ValueError("time_limit_s must be finite.")

    if time_limit < 0.1:
        raise ValueError("time_limit_s must be at least 0.1 seconds.")

    if time_limit > settings.MAX_SOLVER_TIME_S:
        raise ValueError("time_limit_s exceeds the configured maximum.")

    return time_limit


def solve_optimal(
    *,
    file_bytes: bytes,
    budget: float,
    max_items: int | None,
    objective: str,
    lambda_risk: float,
    # scales
    cost_scale: int = 100,
    value_scale: int = 100,
    risk_scale_int: int = 1000,
    time_limit_s: float = 5.0
) -> dict[str, Any]:
    """
    Exact solver using CP-SAT. Handles float inputs by scaling to integers.
    Returns selected items + objective value and totals.
    """
    columns, items, risk_scale = _iter_items(file_bytes)

    if not math.isfinite(budget) or budget <= 0:
        raise ValueError("budget must be a finite number greater than 0.")

    if budget > settings.MAX_NUMERIC_VALUE:
        raise ValueError("budget exceeds the supported numeric range.")

    if not math.isfinite(lambda_risk):
        raise ValueError("lambda_risk must be finite.")

    if lambda_risk < 0 or lambda_risk > settings.MAX_NUMERIC_VALUE:
        raise ValueError("lamba_risk exceeds the supported numeric range.")

    if objective not in {"value", "risk_adjusted_value"}:
        raise ValueError("Unsupported optimization objective.")

    if max_items is not None:
        if max_items <= 0:
            raise ValueError("max_items must be greater than 0.")

        if max_items > settings.MAX_MAX_ITEMS:
            raise ValueError("max_items exceeds the configured maximum.")

    time_limit = _validate_solver_time_limit(time_limit_s)

    # Prepare arrays
    n = len(items)

    if n > settings.MAX_OPTIMIZATION_ROWS:
        raise ValueError("Dataset exceeds the configured optimization row limit.")

    costs_i = []
    values_i = []
    risks_i = []

    for item in items:
        cost = float(item['cost'])
        value = float(item['value'])
        risk = float(item.get('risk', 0.0))
        costs_i.append(_scale_to_int(cost, cost_scale))
        values_i.append(_scale_to_int(value, value_scale))
        risks_i.append(_scale_to_int(risk, risk_scale_int))

    budget_i = _scale_to_int(float(budget), cost_scale)

    model = cp_model.CpModel()
    x = [model.new_bool_var(f"x_{i}") for i in range(n)]

    # Constraints
    model.add(sum(costs_i[i] * x[i] for i in range(n)) <= budget_i)
    if max_items is not None:
        model.add(sum(x[i] for i in range(n)) <= int(max_items))

    if objective == "risk_adjusted_value":
        penalties = []
        for i in range(n):
            pen_float = float(lambda_risk) * (risks_i[i] / risk_scale_int)
            penalties.append(_scale_to_int(pen_float, value_scale))
        obj_terms = [(values_i[i] - penalties[i]) * x[i] for i in range(n)]
    else:
        obj_terms = [values_i[i] * x[i] for i in range(n)]

    model.maximize(sum(obj_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit)
    solver.parameters.num_search_workers = settings.MAX_SOLVER_WORKERS

    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("No feasible solution found within the time limit")

    selected = []
    total_cost_i = 0
    total_value_i = 0
    total_risk = 0.0

    for i in range(n):
        if solver.Value(x[i]) == 1:
            continue

        item = items[i]
        selected.append(item)

        total_cost_i += costs_i[i]
        total_value_i += values_i[i]
        total_risk += float(item.get("risk", 0.0))

    total_cost = total_cost_i / cost_scale
    total_value = total_value_i / value_scale

    result = {
        "method": "cp_sat_optimal_v1",
        "objective": objective,
        "lambda_risk": float(lambda_risk),
        "budget": float(budget),
        "max_items": max_items,
        "risk_scale": risk_scale,
        "summary": {
            "selected_count": len(selected),
            "total_cost": total_cost,
            "total_value": total_value,
            "total_risk": total_risk if any("risk" in item for item in items) else None,
            "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
            "time_limit_s": time_limit,
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


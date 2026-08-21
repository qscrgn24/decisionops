import io

import pytest
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.execute_all import ExecuteAllIn
from app.services.greedy_baseline import _iter_items
from app.services.optimization_guard import (
    GlobalOptimizationBusyError,
    OptimizationExecutionGuard,
    UserOptimizationBusyError,
)
from app.services.optimization_limits import OptimizationLimitError, validate_optimization_dataset


def _valid_csv_bytes() -> bytes:
    return (
        b"name,cost,value,risk\n"
        b"Item A,10,50,0.1\n"
        b"Item B,20,80,0.2\n"
    )


def _upload_dataset(client, *, csv_bytes: bytes | None = None) -> str:
    if csv_bytes is None:
        csv_bytes = _valid_csv_bytes()

    response = client.post("/api/datasets/upload", data={"name": "optimization-test"}, files={"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")})

    assert response.status_code == 200, response.text

    return response.json()["id"]


def test_execute_schema_rejects_nan_budget():
    with pytest.raises(ValidationError):
        ExecuteAllIn(dataset_id="dataset-id", budget=float("nan"))


def test_execute_schema_rejects_infinite_lambda_risk():
    with pytest.raises(ValidationError):
        ExecuteAllIn(dataset_id="dataset-id", budget=100, lambda_risk=float("inf"))


def test_execute_schema_rejects_solver_time_over_limit():
    with pytest.raises(ValidationError):
        ExecuteAllIn(dataset_id="dataset-id", budget=100, time_limit_s=settings.MAX_SOLVER_TIME_S + 0.1)


def test_execute_schema_rejects_max_items_over_limit():
    with pytest.raises(ValidationError):
        ExecuteAllIn(dataset_id="dataset-id", budget=100, max_items=settings.MAX_MAX_ITEMS + 1)


def test_optimization_dataset_rejects_too_many_rows():
    rows = ["name,cost,value"]

    for index in range(settings.MAX_OPTIMIZATION_ROWS + 1):
        rows.append(f"Item {index},10,20")

    csv_bytes = ("\n".join(rows) + "\n").encode()

    with pytest.raises(OptimizationLimitError, match="allowed for optimization"):
        validate_optimization_dataset(csv_bytes, max_rows=settings.MAX_OPTIMIZATION_ROWS)


def test_optimizer_rejects_nan_dataset_value():
    csv_bytes = (
        b"name,cost,value\n"
        b"Item A,10,nan\n"
    )

    with pytest.raises(ValueError, match="value must be a finite number"):
        _iter_items(csv_bytes)


def test_optimizer_rejects_infinite_dataset_cost():
    csv_bytes = (
        b"name,cost,value\n"
        b"Item A,inf,20\n"
    )

    with pytest.raises(ValueError, match="cost must be a finite number"):
        _iter_items(csv_bytes)


def test_optimizer_rejects_excessive_dataset_number():
    excessive_value = (settings.MAX_NUMERIC_VALUE + 1)

    csv_bytes = (
        "name,cost,value\n"
        f"Item A,10,{excessive_value}\n"
    ).encode()

    with pytest.raises(ValueError, match="value exceeds the supported numeric range"):
        _iter_items(csv_bytes)


def test_guard_rejects_second_run_for_same_user():
    guard = OptimizationExecutionGuard(max_global=2)

    with guard.acquire(user_id=1):
        with pytest.raises(UserOptimizationBusyError):
            with guard.acquire(user_id=1):
                pass


def test_guard_rejects_run_when_global_capacity_full():
    guard = OptimizationExecutionGuard(max_global=1)

    with guard.acquire(user_id=1):
        with pytest.raises(GlobalOptimizationBusyError):
            with guard.acquire(user_id=2):
                pass


def test_guard_releases_capacity_after_exception():
    guard = OptimizationExecutionGuard(max_global=1)

    with pytest.raises(RuntimeError):
        with guard.acquire(user_id=1):
            raise RuntimeError("simulated failure")

    with guard.acquire(user_id=2):
        pass


def test_execute_all_hides_internal_error(client, signup_and_login, monkeypatch):
    signup_and_login()

    dataset_id = _upload_dataset(client)

    def fail_greedy(**_kwargs):
        raise RuntimeError("SECRET INTERNAL OPTIMIZER ERROR")

    monkeypatch.setattr("app.api.runs.greedy_select", fail_greedy)

    response = client.post(
        "/api/runs/execute-all",
        json={
            "dataset_id": dataset_id,
            "budget": 100,
            "max_items": 2,
            "objective": "value",
            "lambda_risk": 0,
            "time_limit_s": 1,
        },
    )

    assert response.status_code == 200, response.text

    run = response.json()

    assert run["status"] == "failed"
    assert run["error"] == "Optimization failed."
    assert "SECRET INTERNAL OPTIMIZER ERROR" not in response.text

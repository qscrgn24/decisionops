# ruff: noqa: B008
import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.auth.models import User
from app.auth.session import get_current_user
from app.core.config import settings
from app.db.deps import get_db
from app.dependencies.rate_limit import limit_auth_read, limit_execute, limit_run_create
from app.models.dataset import Dataset
from app.models.run import Run
from app.schemas.execute_all import ExecuteAllIn
from app.schemas.runs import RunCreate, RunOut
from app.services.greedy_baseline import greedy_select
from app.services.optimal_solver import solve_optimal
from app.services.optimization_guard import (
    GlobalOptimizationBusyError,
    UserOptimizationBusyError,
    optimization_guard,
)
from app.services.optimization_limits import OptimizationLimitError, validate_optimization_dataset
from app.services.runs import create_run, delete_run, get_run, update_run

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/runs", tags=["runs"])

@router.post("", response_model=RunOut, dependencies=[Depends(limit_run_create)])
def create_run_endpoint(payload: RunCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Run:
    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id, Dataset.user_id == user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    run = create_run(db, user_id=user.id, dataset_id=payload.dataset_id, config_json=payload.config.model_dump())
    return run


@router.get("/{run_id}", response_model=RunOut, dependencies=[Depends(limit_auth_read)])
def get_run_endpoint(run_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Run:
    run = get_run(db, run_id=run_id, user_id=user.id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run_endpoint(run_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    deleted = delete_run(db, run_id=run_id, user_id=user.id)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/execute-all", response_model=RunOut, dependencies=[Depends(limit_execute )])
def execute_all(payload: ExecuteAllIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Run:
    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id, Dataset.user_id == user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        validate_optimization_dataset(dataset.file_bytes, max_rows=settings.MAX_OPTIMIZATION_ROWS)
    except OptimizationLimitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        with optimization_guard.acquire(user_id=user.id):
            return _execute_optimization(payload=payload, user=user, dataset=dataset, db=db)
    except UserOptimizationBusyError as exc:
        raise HTTPException(status_code=409, detail="An optimization is already running for your account.") from exc
    except GlobalOptimizationBusyError as exc:
        raise HTTPException(status_code=503, detail="Optimization capacity is currently full. Please try again shortly.", headers={"Retry-After": "5"}) from exc


def _execute_optimization(*, payload: ExecuteAllIn, user: User, dataset: Dataset, db: Session) -> Run:
    run = create_run(
            db,
            user_id=user.id,
            dataset_id=payload.dataset_id,
            config_json={
                "budget": payload.budget,
                "max_items": payload.max_items,
                "objective": payload.objective,
                "lambda_risk": payload.lambda_risk,
                "time_limit_s": payload.time_limit_s,
            },
        )

    run.status = "running"
    run.error = None
    update_run(db, run)

    try:
        baseline = greedy_select(
            file_bytes=dataset.file_bytes,
            budget=payload.budget,
            max_items=payload.max_items,
            objective=payload.objective,
            lambda_risk=payload.lambda_risk,
        )

        optimal = solve_optimal(
            file_bytes=dataset.file_bytes,
            budget=payload.budget,
            max_items=payload.max_items,
            objective=payload.objective,
            lambda_risk=payload.lambda_risk,
            time_limit_s=payload.time_limit_s,
        )

        run.result_json = {"baseline": baseline, "optimal": optimal}
        flag_modified(run, "result_json")
        run.status = "succeeded"
        run.error = None
        return update_run(db, run)

    except Exception:
        logger.exception("Optimization execution failed. run_id=%s user_id=%s dataset_id=%s", run.id, user.id, dataset.id)
        run.status = "failed"
        run.result_json = None
        run.error = "Optimization failed."
        return update_run(db, run)

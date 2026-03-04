# ruff: noqa: B008
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.auth.models import User
from app.auth.session import get_current_user
from app.db.deps import get_db
from app.models.dataset import Dataset
from app.models.run import Run
from app.schemas.execute_all import ExecuteAllIn
from app.schemas.runs import RunCreate, RunOut
from app.services.greedy_baseline import greedy_select
from app.services.optimal_solver import solve_optimal
from app.services.runs import create_run, get_run, update_run

router = APIRouter(prefix="/runs", tags=["runs"])

@router.post("", response_model=RunOut)
def create_run_endpoint(payload: RunCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Run:
    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id, Dataset.user_id == user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    run = create_run(db, user_id=user.id, dataset_id=payload.dataset_id, config_json=payload.config.model_dump())
    return run


@router.get("/{run_id}", response_model=RunOut)
def get_run_endpoint(run_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Run:
    run = get_run(db, run_id=run_id, user_id=user.id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/execute-all", response_model=RunOut)
def execute_all(payload: ExecuteAllIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Run:
    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id, Dataset.user_id == user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    run=create_run(
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

    # 2) Mark Running
    run.status = "running"
    run.error = None
    update_run(db, run)

    try:
        cfg = run.config_json
        budget = float(cfg["budget"])
        max_items = cfg.get("max_items", None)
        if max_items is not None:
            max_items = int(max_items)

        objective = cfg.get("objective", "value")
        lambda_risk = float(cfg.get("lambda_risk", 0.0))
        time_limit_s = float(cfg.get("time_limit_s", 5.0))

        file_bytes = dataset.file_bytes

        # 3) Greedy baseline
        baseline = greedy_select(
            file_bytes=file_bytes,
            budget=budget,
            max_items=max_items,
            objective=objective,
            lambda_risk=lambda_risk,
        )

        # 4) Optimal solver
        optimal = solve_optimal(
            file_bytes=file_bytes,
            budget=budget,
            max_items=max_items,
            objective=objective,
            lambda_risk=lambda_risk,
            time_limit_s=time_limit_s,
        )

        # 5) Store results (merge + flag modified)
        run.result_json = {"baseline": baseline, "optimal": optimal}
        flag_modified(run, "result_json")
        run.status = "succeeded"
        update_run(db, run)
        return run
    
    except Exception as e:
        run.status = "failed"
        run.error = str(e)[:500]
        update_run(db, run)
        return run
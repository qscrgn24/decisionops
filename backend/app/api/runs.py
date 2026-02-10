from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.db.deps import get_db
from app.schemas.runs import RunCreate, RunOut
from app.services.runs import get_run, update_run
from app.models.run import Run
from app.services.greedy_baseline import greedy_select
from app.services.optimal_solver import solve_optimal
from app.schemas.execute_all import ExecuteAllIn

router = APIRouter(prefix="/runs", tags=["runs"])

@router.post("", response_model=RunOut)
def create_run_endpoint(payload: RunCreate, db=Depends(get_db)):
    import uuid

    run = Run(id=str(uuid.uuid4()), dataset_id=payload.dataset_id, status="created", config_json=payload.config.model_dump(), result_json=None, error=None)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("/{run_id}", response_model=RunOut)
def get_run_endpoint(run_id, db=Depends(get_db)):
    run = get_run(db, run_id=run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/execute-all", response_model=RunOut)
def execute_all(payload: ExecuteAllIn, db: Session = Depends(get_db)):
    import uuid

    # 1) Create Run
    run = Run(
        id=str(uuid.uuid4()),
        dataset_id=payload.dataset_id,
        status="created",
        config_json={
            "budget": payload.budget,
            "max_items": payload.max_items,
            "lambda_risk": payload.lambda_risk,
            "objective": payload.objective,
            "time_limit_s": payload.time_limit_s,
        },
        result_json=None,
        error=None,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # 2) Mark Running
    run.status = "running"
    run.error = None
    update_run(db, run)

    file_path = Path("storage/uploads") / f"{run.dataset_id}.csv"

    try:
        cfg = run.config_json
        budget = float(cfg["budget"])
        max_items = cfg.get("max_items", None)
        if max_items is not None:
            max_items = int(max_items)

        objective = cfg.get("objective", "value")
        lambda_risk = float(cfg.get("lambda_risk", 0.0))
        time_limit_s = float(cfg.get("time_limit_s", 5.0))

        # 3) Greedy baseline
        baseline = greedy_select(
            file_path=file_path,
            budget=budget,
            max_items=max_items,
            objective=objective,
            lambda_risk=lambda_risk,
        )

        # 4) Optimal solver
        optimal = solve_optimal(
            file_path=file_path,
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
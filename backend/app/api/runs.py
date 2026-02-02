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


@router.post("/{run_id}/execute-greedy", response_model=RunOut)
def execute_greedy(run_id: str, db: Session = Depends(get_db)):
    run = get_run(db, run_id=run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    
    if not run.config_json:
        raise HTTPException(status_code=400, detail="Run has no congif_json")
    
    # Mark Running
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

        file_path = Path("storage/uploads") / f"{run.dataset_id}.csv"

        result = greedy_select(file_path=file_path, budget=budget, max_items=max_items, objective=objective, lambda_risk=lambda_risk)

        run.result_json = {"baseline": result}
        run.status = "succeeded"
        update_run(db, run)
        return run
    
    except Exception as e:
        run.status = "failed"
        run.error = str(e)[:500]
        update_run(db, run)
        return run
    

@router.post("/{run_id}/execute-optimal", response_model=RunOut)
def execute_optimal(run_id: str, db: Session = Depends(get_db)):
    run = get_run(db, run_id=run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if not run.config_json:
        raise HTTPException(status_code=400, detail="Run has no config_json")
    
    # Mark Running
    run.status = "running"
    run.error = None
    update_run(db, run)

    try:
        cfg = run.config_json
        budget = float(cfg['budget'])
        max_items = cfg.get("max_items", None)
        if max_items is not None:
            max_items = int(max_items)

        objective = cfg.get("objective", "value")
        lambda_risk = float(cfg.get("lambda_risk", 0.0))

        file_path = Path("storage/uploads") / f"{run.dataset_id}.csv"

        optimal = solve_optimal(
            file_path=file_path,
            budget=budget,
            max_items=max_items,
            objective=objective,
            lambda_risk=lambda_risk,
            time_limit_s=5.0,
        )

        existing = run.result_json or {}
        run.result_json = {**existing, "optimal": optimal}
        flag_modified(run, "result_json")


        run.status = "succeeded"
        update_run(db, run)
        return run
    
    except Exception as e:
        run.status = "failed"
        run.error = str(e)[:500]
        update_run(db, run)
        return run
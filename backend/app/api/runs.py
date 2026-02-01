from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.runs import RunCreate, RunOut
from app.services.runs import create_run, get_run

router = APIRouter(prefix="/runs", tags=["runs"])

@router.post("", response_model=RunOut)
def create_run_endpoint(payload: RunCreate, db=Depends(get_db)):
    return create_run(db, dataset_id=payload.dataset_id)

@router.get("/{run_id}", response_model=RunOut)
def get_run_endpoint(run_id, db=Depends(get_db)):
    run = get_run(db, run_id=run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
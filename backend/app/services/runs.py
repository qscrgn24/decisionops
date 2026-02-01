import uuid
from sqlalchemy.orm import Session

from app.models.run import Run

def create_run(db: Session, *, dataset_id: str):
    run = Run(id=str(uuid.uuid4()), dataset_id=dataset_id, status="created")
    db.add(run)
    db.commit()
    db.refresh(run)
    return run

def get_run(db: Session, *, run_id: str):
    return db.get(Run, run_id)
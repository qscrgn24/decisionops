from sqlalchemy.orm import Session

from app.models.run import Run


def get_run(db: Session, *, run_id: str):
    return db.get(Run, run_id)


def update_run(db: Session, run: Run):
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
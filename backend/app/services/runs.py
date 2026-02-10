from __future__ import annotations

import uuid
from sqlalchemy.orm import Session

from app.models.run import Run


def create_run(
    db: Session,
    *,
    user_id: int,
    dataset_id: str,
    config_json: dict,
):
    run=Run(
        id=str(uuid.uuid4()),
        user_id=user_id,
        dataset_id=dataset_id,
        status="created",
        config_json=config_json,
        result_json=None,
        error=None,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_run(db: Session, *, run_id: str, user_id: int):
    return db.query(Run).filter(Run.id == run_id, Run.user_id == user_id).first()


def update_run(db: Session, run: Run):
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
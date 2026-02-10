import os
import uuid
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.dataset import Dataset

UPLOAD_DIR = Path("storage/uploads")

def create_dataset(
    db: Session,
    *,
    user_id: int,
    name:str,
    original_filename: str,
    file_bytes
):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    dataset_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{dataset_id}.csv"

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    dataset = Dataset(
        id=dataset_id,
        name=name,
        original_filename=original_filename,
        user_id=user_id,
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset
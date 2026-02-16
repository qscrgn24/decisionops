import uuid
from sqlalchemy.orm import Session

from app.models.dataset import Dataset

def create_dataset(
    db: Session,
    *,
    user_id: int,
    name:str,
    original_filename: str,
    file_bytes: bytes,
):
    dataset_id = str(uuid.uuid4())

    dataset = Dataset(
        id=dataset_id,
        name=name,
        original_filename=original_filename,
        user_id=user_id,
        file_bytes=file_bytes,
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset
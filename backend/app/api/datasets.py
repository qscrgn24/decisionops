from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.datasets import DatasetOut
from app.services.datasets import create_dataset
from app.schemas.dataset_preview import DatasetPreviewOut
from app.services.dataset_preview import preview_and_validate_csv
from app.auth.session import get_current_user
from app.auth.models import User
from app.models.dataset import Dataset

router = APIRouter(prefix="/datasets", tags=["datasets"])

@router.post("/upload", response_model=DatasetOut)
async def upload_dataset(
    name: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required.")
    
    # Basic CSV check (MVP)
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    dataset = create_dataset(
        db,
        user_id=user.id,
        name=name,
        original_filename=file.filename,
        file_bytes=content
    )

    return dataset


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewOut)
def preview_dataset(dataset_id: str, n: int = 20, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    try:
        res = preview_and_validate_csv(dataset.file_bytes, n=n)
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to preview dataset.")
    
    return DatasetPreviewOut(
        dataset_id=dataset_id,
        columns=res.columns,
        total_rows=res.total_rows,
        has_category=res.has_category,
        has_risk=res.has_risk,
        risk_scale=res.risk_scale,
        resolved_columns=res.resolved_columns,
        missing_required=res.missing_required,
        rows=res.rows,
        warnings=res.warnings
    )
# ruff: noqa: B008
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.session import get_current_user
from app.core.config import settings
from app.db.deps import get_db
from app.dependencies.rate_limit import limit_preview, limit_upload
from app.models.dataset import Dataset
from app.schemas.dataset_preview import DatasetPreviewOut
from app.schemas.datasets import DatasetOut
from app.services.csv_upload import (
    CSVValidationError,
    UploadTooLargeError,
    read_bounded_upload,
    validate_csv_structure,
)
from app.services.dataset_preview import preview_and_validate_csv
from app.services.datasets import create_dataset

router = APIRouter(prefix="/datasets", tags=["datasets"])

@router.post("/upload", response_model=DatasetOut, dependencies=[Depends(limit_upload)])
async def upload_dataset(
    name: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dataset:
    dataset_name = name.strip()

    if not dataset_name:
        raise HTTPException(status_code=400, detail="Dataset name is required.")

    if len(dataset_name) > settings.MAX_DATASET_NAME_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"Dataset name exceeds maximum length of {settings.MAX_DATASET_NAME_CHARS} characters.",
        )
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required.")

    filename = file.filename.strip()

    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    if len(filename) > settings.MAX_FILENAME_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"Filename exceeds maximum length of {settings.MAX_FILENAME_CHARS} characters.",
        )
    
    # Basic CSV check (MVP)
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    try:
        content = await read_bounded_upload(file, max_bytes=settings.MAX_UPLOAD_BYTES)
    except UploadTooLargeError as exc:
        raise HTTPException(
            status_code=413,
            detail="Uploaded CSV file is too large.",
        ) from exc

    try:
        validate_csv_structure(
            content,
            max_rows=settings.MAX_DATASET_ROWS,
            max_columns=settings.MAX_DATASET_COLUMNS,
            max_cell_chars=settings.MAX_CELL_CHARS,
        )
    except CSVValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    dataset = create_dataset(
        db,
        user_id=user.id,
        name=dataset_name,
        original_filename=filename,
        file_bytes=content
    )

    return dataset


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewOut, dependencies=[Depends(limit_preview)])
def preview_dataset(dataset_id: str, n: int = 20, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DatasetPreviewOut:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    try:
        res = preview_and_validate_csv(dataset.file_bytes, n=n)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Failed to preview dataset.") from exc

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
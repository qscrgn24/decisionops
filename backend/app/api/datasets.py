from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from pathlib import Path

from app.db.deps import get_db
from app.schemas.datasets import DatasetOut
from app.services.datasets import create_dataset
from app.schemas.dataset_preview import DatasetPreviewOut
from app.services.dataset_preview import preview_and_validate_csv

router = APIRouter(prefix="/datasets", tags=["datasets"])

@router.post("/upload", response_model=DatasetOut)
async def upload_dataset(
    name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
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
        name=name,
        original_filename=file.filename,
        file_bytes=content
    )

    return dataset


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewOut)
def preview_dataset(dataset_id, n: int = 20):
    file_path = Path("storage/uploads") / f"{dataset_id}.csv"

    try:
        res = preview_and_validate_csv(file_path, n=n)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset file not found.")
    
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
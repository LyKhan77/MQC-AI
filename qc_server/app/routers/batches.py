import os
import shutil

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import settings as app_settings
from ..database import SessionLocal, get_db
from ..models import Batch, Defect, Image
from ..schemas import (
    BatchCreate,
    BatchCreateResponse,
    BatchPatch,
    BatchResult,
    BatchRunRequest,
    BatchStatusOut,
    BatchSummary,
    ImageOut,
    ImagePatch,
)
from ..services import job_queue
from ..services.pipeline import prepare_images, run_batch
from ..util import gen_id, now_iso
from .settings import get_or_create_setting

router = APIRouter(prefix="/api/batches", tags=["batches"])


@router.post("", response_model=BatchCreateResponse, status_code=201)
def submit_batch(payload: BatchCreate, db: Session = Depends(get_db)):
    # Creates the batch in a "pending" state. Segmentation is started
    # separately via POST /batches/{id}/run (the QC Studio "Load Batch" step).
    setting = get_or_create_setting(db)
    batch_id = gen_id("batch")
    job_id = gen_id("job")
    batch = Batch(
        id=batch_id,
        name=payload.batch_name,
        source_path=payload.source_path,
        camera_id=payload.camera_id,
        created_at=now_iso(),
        status="pending",
        model_info={
            "detection": setting.detection_model,
            "segmentation": setting.segmentation_model,
            "confidence": setting.confidence_threshold,
            "strategy": setting.defect_strategy,
        },
    )
    db.add(batch)
    db.commit()
    prepare_images(db, batch)
    return BatchCreateResponse(batch_id=batch_id, job_id=job_id)


@router.post("/{batch_id}/run", response_model=BatchStatusOut)
def run_batch_endpoint(batch_id: str, payload: BatchRunRequest,
                       background: BackgroundTasks, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "batch not found")
    if batch.status != "pending":
        raise HTTPException(409, "batch is not pending")
    batch.status = "processing"
    if payload.confidence_threshold is not None and isinstance(batch.model_info, dict):
        info = dict(batch.model_info)
        info["confidence"] = payload.confidence_threshold
        batch.model_info = info
    db.commit()
    job_queue.set_total(batch_id, 0)
    background.add_task(run_batch, batch_id, SessionLocal, payload.confidence_threshold)
    return BatchStatusOut(batch_id=batch_id, status="processing",
                          progress=job_queue.get(batch_id))


@router.get("", response_model=list[BatchSummary])
def list_batches(db: Session = Depends(get_db)):
    batches = db.query(Batch).order_by(Batch.created_at.desc()).all()
    reviewed_counts = dict(
        db.query(Image.batch_id, func.count(Image.id))
        .filter(Image.reviewed.is_(True))
        .group_by(Image.batch_id)
        .all()
    )
    return [
        BatchSummary(
            id=b.id, name=b.name, source_path=b.source_path, camera_id=b.camera_id,
            created_at=b.created_at, image_count=b.image_count, defect_count=b.defect_count,
            status=b.status, reviewer=b.reviewer, model_info=b.model_info,
            reviewed_count=reviewed_counts.get(b.id, 0),
        )
        for b in batches
    ]


@router.get("/{batch_id}/status", response_model=BatchStatusOut)
def batch_status(batch_id: str, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "batch not found")
    return BatchStatusOut(batch_id=batch_id, status=batch.status,
                          progress=job_queue.get(batch_id))


@router.get("/{batch_id}", response_model=BatchResult)
def get_batch(batch_id: str, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "batch not found")
    images = db.query(Image).filter(Image.batch_id == batch_id).all()
    return BatchResult(
        batch_name=batch.name,
        source_path=batch.source_path,
        images=[ImageOut.model_validate(im) for im in images],
    )


@router.patch("/{batch_id}", response_model=BatchSummary)
def patch_batch(batch_id: str, payload: BatchPatch, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "batch not found")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(batch, key, value)
    db.commit()
    db.refresh(batch)
    return batch


@router.delete("/{batch_id}")
def delete_batch(batch_id: str, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "batch not found")
    image_ids = [i.id for i in db.query(Image).filter(Image.batch_id == batch_id).all()]
    if image_ids:
        db.query(Defect).filter(Defect.image_id.in_(image_ids)).delete(synchronize_session=False)
    db.query(Image).filter(Image.batch_id == batch_id).delete(synchronize_session=False)
    db.delete(batch)
    db.commit()
    shutil.rmtree(os.path.join(app_settings.data_dir, "batches", batch_id), ignore_errors=True)
    return {"deleted": batch_id}


@router.patch("/{batch_id}/images/{image_id}", response_model=ImageOut)
def patch_image(batch_id: str, image_id: str, payload: ImagePatch,
                db: Session = Depends(get_db)):
    image = db.get(Image, image_id)
    if not image or image.batch_id != batch_id:
        raise HTTPException(404, "image not found")
    image.reviewed = payload.reviewed
    db.commit()
    db.refresh(image)
    return ImageOut.model_validate(image)

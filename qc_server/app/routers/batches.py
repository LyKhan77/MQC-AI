from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import SessionLocal, get_db
from ..models import Batch, Image
from ..schemas import (
    BatchCreate,
    BatchCreateResponse,
    BatchPatch,
    BatchResult,
    BatchStatusOut,
    BatchSummary,
    ImageOut,
    ImagePatch,
)
from ..services import job_queue
from ..services.pipeline import run_batch
from ..util import gen_id, now_iso
from .settings import get_or_create_setting

router = APIRouter(prefix="/api/batches", tags=["batches"])


@router.post("", response_model=BatchCreateResponse, status_code=201)
def submit_batch(payload: BatchCreate, background: BackgroundTasks,
                 db: Session = Depends(get_db)):
    setting = get_or_create_setting(db)
    batch_id = gen_id("batch")
    job_id = gen_id("job")
    batch = Batch(
        id=batch_id,
        name=payload.batch_name,
        source_path=payload.source_path,
        camera_id=payload.camera_id,
        created_at=now_iso(),
        status="processing",
        model_info={
            "detection": setting.detection_model,
            "segmentation": setting.segmentation_model,
            "confidence": setting.confidence_threshold,
            "strategy": setting.defect_strategy,
        },
    )
    db.add(batch)
    db.commit()
    job_queue.set_total(batch_id, 0)
    background.add_task(run_batch, batch_id, SessionLocal)
    return BatchCreateResponse(batch_id=batch_id, job_id=job_id)


@router.get("", response_model=list[BatchSummary])
def list_batches(db: Session = Depends(get_db)):
    return db.query(Batch).order_by(Batch.created_at.desc()).all()


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

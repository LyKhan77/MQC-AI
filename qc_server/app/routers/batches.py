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
    DefectCreate,
    DefectOut,
    DefectPatch,
    ImageOut,
    ImagePatch,
    SegmentRequest,
    SegmentResponse,
)
from ..services import job_queue
from ..services.pipeline import prepare_images, run_batch
from ..util import gen_id, now_iso
from .settings import get_or_create_setting

router = APIRouter(prefix="/api/batches", tags=["batches"])


def _batch_image(db: Session, batch_id: str, image_id: str) -> Image:
    image = db.get(Image, image_id)
    if not image or image.batch_id != batch_id:
        raise HTTPException(404, "image not found")
    return image


def _defect_for_image(db: Session, image_id: str, defect_id: str) -> Defect:
    defect = db.get(Defect, defect_id)
    if not defect or defect.image_id != image_id:
        raise HTTPException(404, "defect not found")
    return defect


def _recompute_defects(db: Session, batch_id: str, image: Image):
    db.flush()
    image_count = db.query(func.count(Defect.id)).filter(Defect.image_id == image.id).scalar() or 0
    image.status = "defect" if image_count else "clean"
    batch = db.get(Batch, batch_id)
    batch.defect_count = (
        db.query(func.count(Defect.id))
        .join(Image, Defect.image_id == Image.id)
        .filter(Image.batch_id == batch_id)
        .scalar()
        or 0
    )


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
    if batch.status == "processing":
        raise HTTPException(409, "batch already processing")
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


@router.post("/{batch_id}/reset", response_model=BatchStatusOut)
def reset_batch(batch_id: str, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "batch not found")
    if batch.status == "processing":
        raise HTTPException(409, "batch is processing")
    images = db.query(Image).filter(Image.batch_id == batch_id).all()
    for image in images:
        image.defects.clear()
        image.status = "pending"
        image.reviewed = False
    batch.status = "pending"
    batch.defect_count = 0
    batch.reviewer = None
    batch.error = None
    db.commit()
    return BatchStatusOut(batch_id=batch_id, status="pending",
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


@router.post("/{batch_id}/images/{image_id}/defects", response_model=DefectOut,
             status_code=201)
def create_defect(batch_id: str, image_id: str, payload: DefectCreate,
                  db: Session = Depends(get_db)):
    image = _batch_image(db, batch_id, image_id)
    defect = Defect(
        id=gen_id("d"),
        image_id=image.id,
        type=payload.type,
        category=payload.category,
        confidence=1.0,
        polygon=payload.polygon,
    )
    db.add(defect)
    _recompute_defects(db, batch_id, image)
    db.commit()
    db.refresh(defect)
    return DefectOut.model_validate(defect)


@router.patch("/{batch_id}/images/{image_id}/defects/{defect_id}",
              response_model=DefectOut)
def patch_defect(batch_id: str, image_id: str, defect_id: str, payload: DefectPatch,
                 db: Session = Depends(get_db)):
    image = _batch_image(db, batch_id, image_id)
    defect = _defect_for_image(db, image.id, defect_id)
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(defect, key, value)
    _recompute_defects(db, batch_id, image)
    db.commit()
    db.refresh(defect)
    return DefectOut.model_validate(defect)


@router.delete("/{batch_id}/images/{image_id}/defects/{defect_id}")
def delete_defect(batch_id: str, image_id: str, defect_id: str,
                  db: Session = Depends(get_db)):
    image = _batch_image(db, batch_id, image_id)
    defect = _defect_for_image(db, image.id, defect_id)
    db.delete(defect)
    _recompute_defects(db, batch_id, image)
    db.commit()
    return {"deleted": defect_id}


@router.post("/{batch_id}/images/{image_id}/segment", response_model=SegmentResponse)
def segment_image(batch_id: str, image_id: str, payload: SegmentRequest,
                  db: Session = Depends(get_db)):
    image = _batch_image(db, batch_id, image_id)
    has_point = payload.point is not None
    has_box = payload.box is not None
    if has_point == has_box:
        raise HTTPException(400, "provide point or box")
    if has_point and len(payload.point) != 2:
        raise HTTPException(400, "point must be [x,y]")
    if has_box and len(payload.box) != 4:
        raise HTTPException(400, "box must be [x1,y1,x2,y2]")

    setting = get_or_create_setting(db)
    if not setting.qc_model:
        raise HTTPException(409, "model not configured")
    model_path = os.path.join(app_settings.models_dir, setting.qc_model)
    batch = db.get(Batch, batch_id)
    image_path = os.path.join(batch.source_path, image.filename)
    from ..services.inference import sam_interactive

    try:
        polygon = sam_interactive.segment(
            image_path, image.width, image.height, payload.point, payload.box, model_path
        )
    except ValueError as e:
        raise HTTPException(409, str(e)) from e
    return SegmentResponse(polygon=polygon)


@router.delete("/{batch_id}/images/{image_id}")
def delete_image(batch_id: str, image_id: str, db: Session = Depends(get_db)):
    image = db.get(Image, image_id)
    if not image or image.batch_id != batch_id:
        raise HTTPException(404, "image not found")
    batch = db.get(Batch, batch_id)
    path = os.path.join(batch.source_path, image.filename)
    if os.path.exists(path):
        os.remove(path)
    db.delete(image)
    db.commit()
    batch.image_count = db.query(Image).filter(Image.batch_id == batch_id).count()
    db.commit()
    return {"deleted": image_id}

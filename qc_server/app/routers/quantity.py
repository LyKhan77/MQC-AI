import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import QuantityCheck
from ..schemas import QuantityCheckIn, QuantityCheckOut, QuantityDetectOut
from ..services.object_detection import detect, resolve_named_model_path, serialize_detections
from ..services.quantity import per_class_counts
from ..util import gen_id, now_iso
from .settings import get_or_create_setting

router = APIRouter(prefix="/api/quantity", tags=["quantity"])


@router.post("/detect/image", response_model=QuantityDetectOut)
async def detect_quantity_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    setting = get_or_create_setting(db)
    model_path = resolve_named_model_path(setting.quantity_model)
    if not model_path:
        raise HTTPException(409, "quantity model not configured")
    raw = await file.read()
    frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, "invalid image")
    detections = detect(frame, setting.quantity_confidence_threshold, model_path)
    h, w = frame.shape[:2]
    return {
        "total": len(detections),
        "per_class": per_class_counts(detections),
        "detections": serialize_detections(detections),
        "width": int(w),
        "height": int(h),
    }


@router.post("/checks", response_model=QuantityCheckOut, status_code=201)
def create_check(payload: QuantityCheckIn, db: Session = Depends(get_db)):
    check = QuantityCheck(id=gen_id("qty"), created_at=now_iso(), **payload.model_dump())
    db.add(check)
    db.commit()
    db.refresh(check)
    return check


@router.get("/checks", response_model=list[QuantityCheckOut])
def list_checks(db: Session = Depends(get_db)):
    return db.query(QuantityCheck).order_by(QuantityCheck.created_at.desc()).all()


@router.get("/checks/{check_id}", response_model=QuantityCheckOut)
def get_check(check_id: str, db: Session = Depends(get_db)):
    check = db.get(QuantityCheck, check_id)
    if not check:
        raise HTTPException(404, "not found")
    return check

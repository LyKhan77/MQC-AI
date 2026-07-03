import os
import shutil
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import settings as app_settings
from ..database import get_db
from ..models import Batch, Camera, DefectClass
from ..services.autocrop import autocrop
from ..services.inference.base import DefectClassSpec, get_strategy
from ..services.pipeline import prepare_images
from ..services.streaming import grab_one
from ..util import gen_id, now_iso
from .settings import get_or_create_setting

router = APIRouter(prefix="/api/inspection", tags=["inspection"])

_INSPECTION = "inspection"


def _tmp_base() -> Path:
    return Path(app_settings.data_dir, _INSPECTION, "_tmp").resolve()


def _detect_frame(frame, setting, db):
    key = gen_id("ins")
    tmp_dir = _tmp_base() / key
    os.makedirs(tmp_dir, exist_ok=True)
    frame_path = tmp_dir / "frame.jpg"
    cv2.imwrite(str(frame_path), frame)

    h, w = frame.shape[:2]
    specs = [DefectClassSpec(c.name, c.category, c.enabled) for c in db.query(DefectClass).all()]
    qc_model = setting.qc_model or ""
    params = {
        "confidence_threshold": setting.qc_confidence_threshold,
        "qc_model_path": os.path.join(app_settings.models_dir, qc_model) if qc_model else "",
    }
    detections = get_strategy(setting.defect_strategy).detect(str(frame_path), int(w), int(h), specs, params)
    defects = [
        {
            "type": det.type,
            "category": det.category,
            "confidence": round(det.confidence, 3),
            "polygon": det.polygon,
        }
        for det in detections
    ]
    return {
        "key": key,
        "width": int(w),
        "height": int(h),
        "verdict": "defect" if defects else "clean",
        "defects": defects,
        "frame_url": f"/api/inspection/frame/{key}/frame.jpg",
    }


@router.post("/detect")
async def detect_inspection(
    file: UploadFile | None = File(default=None),
    camera_id: str | None = Form(default=None),
    crop_mode: str = Form(default="full"),
    db: Session = Depends(get_db),
):
    if crop_mode not in {"full", "auto"}:
        raise HTTPException(400, "invalid crop mode")

    if file is not None:
        raw = await file.read()
        frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise HTTPException(400, "invalid image")
    elif camera_id:
        camera = db.get(Camera, camera_id)
        if not camera:
            raise HTTPException(404, "camera not found")
        frame = grab_one(camera.source)
        if frame is None:
            raise HTTPException(503, "camera frame unavailable")
    else:
        raise HTTPException(400, "file or camera_id required")

    if crop_mode == "auto":
        frame, _ = autocrop(frame)

    result = _detect_frame(frame, get_or_create_setting(db), db)
    result["crop_mode"] = crop_mode
    return result


@router.get("/frame/{key}/frame.jpg")
def serve_frame(key: str):
    base = Path(app_settings.data_dir, _INSPECTION).resolve()
    path = (base / "_tmp" / os.path.basename(key) / "frame.jpg").resolve()
    try:
        path.relative_to(base)
    except ValueError:
        raise HTTPException(404, "not found")
    if not path.is_file():
        raise HTTPException(404, "not found")
    return FileResponse(path)


class ToQcIn(BaseModel):
    keys: list[str] = []


@router.post("/to-qc", status_code=201)
def inspection_to_qc(payload: ToQcIn, db: Session = Depends(get_db)):
    tmp_base = _tmp_base()
    batch_id = gen_id("batch")
    dest = os.path.join(app_settings.data_dir, "batches", batch_id)
    os.makedirs(dest, exist_ok=True)
    count = 0

    for key in payload.keys:
        src_dir = (tmp_base / (key or "")).resolve()
        try:
            src_dir.relative_to(tmp_base)
        except ValueError:
            continue
        if src_dir == tmp_base:
            continue
        src = src_dir / "frame.jpg"
        if src.is_file():
            shutil.move(str(src), os.path.join(dest, f"{src_dir.name}.jpg"))
            shutil.rmtree(str(src_dir), ignore_errors=True)
            count += 1

    if count == 0:
        shutil.rmtree(dest, ignore_errors=True)
        raise HTTPException(400, "no captures to send")

    setting = get_or_create_setting(db)
    batch = Batch(
        id=batch_id,
        name=f"direct_{batch_id[-6:]}",
        source_path=dest,
        camera_id=None,
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
    return {"batch_id": batch_id}

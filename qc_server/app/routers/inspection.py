import os
import shutil
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import storage
from ..config import settings as app_settings
from ..database import get_db
from ..models import Batch, Camera, Defect, DefectClass, Image
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


def _detect_frame(frame, setting, db, debug_frame=None):
    key = gen_id("ins")
    tmp_dir = _tmp_base() / key
    os.makedirs(tmp_dir, exist_ok=True)
    frame_path = tmp_dir / "frame.jpg"
    cv2.imwrite(str(frame_path), frame)
    if debug_frame is not None:
        cv2.imwrite(str(tmp_dir / "debug.jpg"), debug_frame)

    h, w = frame.shape[:2]
    specs = [DefectClassSpec(c.name, c.category, c.enabled) for c in db.query(DefectClass).all()]
    qc_model = setting.qc_model or ""
    params = {
        "confidence_threshold": setting.qc_confidence_threshold,
        "qc_model_path": os.path.join(app_settings.models_dir, qc_model) if qc_model else "",
        "qc_device": setting.qc_device,
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
        "debug_frame_url": f"/api/inspection/frame/{key}/debug.jpg" if debug_frame is not None else None,
    }


@router.post("/detect")
async def detect_inspection(
    file: UploadFile | None = File(default=None),
    camera_id: str | None = Form(default=None),
    crop_mode: str = Form(default="full"),
    debug_crop: bool = Form(default=False),
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

    debug_frame = None
    if crop_mode == "auto":
        original = frame.copy()
        frame, box = autocrop(frame)
        if debug_crop:
            debug_frame = original
            if box:
                x1, y1, x2, y2 = box
                thickness = max(2, min(original.shape[:2]) // 200)
                cv2.rectangle(debug_frame, (x1, y1), (max(x1, x2 - 1), max(y1, y2 - 1)), (0, 255, 255), thickness)
                cv2.putText(debug_frame, "AUTO-CROP", (x1, max(24, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
            else:
                cv2.putText(debug_frame, "FULL FRAME FALLBACK", (16, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2, cv2.LINE_AA)

    result = _detect_frame(frame, get_or_create_setting(db), db, debug_frame)
    result["crop_mode"] = crop_mode
    return result


def _serve_frame_file(key: str, filename: str):
    if filename not in {"frame.jpg", "debug.jpg"}:
        raise HTTPException(404, "not found")
    base = Path(app_settings.data_dir, _INSPECTION).resolve()
    path = (base / "_tmp" / os.path.basename(key) / filename).resolve()
    try:
        path.relative_to(base)
    except ValueError:
        raise HTTPException(404, "not found")
    if not path.is_file():
        raise HTTPException(404, "not found")
    return FileResponse(path)


@router.get("/frame/{key}/frame.jpg")
def serve_frame(key: str):
    return _serve_frame_file(key, "frame.jpg")


@router.get("/frame/{key}/debug.jpg")
def serve_debug_frame(key: str):
    return _serve_frame_file(key, "debug.jpg")


class ToQcIn(BaseModel):
    captures: list[dict] = []


@router.post("/to-qc", status_code=201)
def inspection_to_qc(payload: ToQcIn, db: Session = Depends(get_db)):
    tmp_base = _tmp_base()
    batch_id = gen_id("batch")
    dest = os.path.join(app_settings.data_dir, "batches", batch_id)
    os.makedirs(dest, exist_ok=True)
    count = 0
    defects_by_key = {}

    for capture in payload.captures:
        key = capture.get("key") or ""
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
            defects_by_key[src_dir.name] = capture.get("defects") or []

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
        status="done",
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
    defect_count = 0
    for image in db.query(Image).filter(Image.batch_id == batch.id).all():
        key = os.path.splitext(image.filename)[0]
        defects = defects_by_key.get(key, [])
        for item in defects:
            db.add(Defect(
                id=gen_id("d"),
                image_id=image.id,
                type=item.get("type", ""),
                category=item.get("category", ""),
                confidence=float(item.get("confidence", 0)),
                polygon=item.get("polygon", []),
            ))
        image.status = "defect" if defects else "clean"
        defect_count += len(defects)
    batch.defect_count = defect_count
    db.commit()
    storage.write_result_json(db, batch)
    return {"batch_id": batch_id}

import os
import shutil
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..config import settings as app_settings
from ..database import get_db
from ..models import QuantityCheck
from ..schemas import QuantityCheckIn, QuantityCheckOut, QuantityDetectOut
from ..services.crop import crop_objects
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
    detections = detect(
        frame,
        setting.quantity_confidence_threshold,
        model_path,
        iou=setting.quantity_nms_iou,
        agnostic_nms=setting.quantity_agnostic_nms,
    )
    h, w = frame.shape[:2]
    crop_key = gen_id("qtmp")
    tmp_dir = os.path.join(app_settings.data_dir, "quantity", "_tmp", crop_key)
    files = crop_objects(frame, detections, tmp_dir)
    kept = [d for d in detections if d.x2 > d.x1 and d.y2 > d.y1]
    crops = [
        {
            "file": f,
            "label": kept[i].label if i < len(kept) else "",
            "url": f"/api/quantity/crops/_tmp/{crop_key}/{f}",
        }
        for i, f in enumerate(files)
    ]
    return {
        "total": len(detections),
        "per_class": per_class_counts(detections),
        "detections": serialize_detections(detections),
        "width": int(w),
        "height": int(h),
        "crop_key": crop_key,
        "crops": crops,
    }


@router.get("/crops/{p1}/{p2}/{filename}")
def serve_quantity_crop(p1: str, p2: str, filename: str):
    base = Path(app_settings.data_dir, "quantity").resolve()
    path = Path(base, p1, p2, os.path.basename(filename)).resolve()
    try:
        path.relative_to(base)
    except ValueError:
        raise HTTPException(404, "not found")
    if not path.is_file():
        raise HTTPException(404, "not found")
    return FileResponse(path)


@router.post("/checks", response_model=QuantityCheckOut, status_code=201)
def create_check(payload: QuantityCheckIn, db: Session = Depends(get_db)):
    check_id = gen_id("qty")
    data = payload.model_dump()
    inputs = data.pop("inputs", []) or []
    q_base = os.path.join(app_settings.data_dir, "quantity")
    persisted = []
    tmp_base = Path(q_base, "_tmp").resolve()
    for idx, inp in enumerate(inputs):
        crop_key = inp.pop("crop_key", None)
        files = inp.get("crops", []) or []
        # Contain the source dir strictly within _tmp so a crafted crop_key cannot
        # traverse outside and move arbitrary files (path-traversal guard).
        src_dir = Path(tmp_base, crop_key or "").resolve()
        contained = False
        try:
            src_dir.relative_to(tmp_base)
            contained = src_dir != tmp_base
        except ValueError:
            contained = False
        if crop_key and files and contained and src_dir.is_dir():
            dest = os.path.join(q_base, check_id, str(idx))
            os.makedirs(dest, exist_ok=True)
            urls = []
            for f in files:
                name = os.path.basename(f)
                src = os.path.join(str(src_dir), name)
                if os.path.isfile(src):
                    shutil.move(src, os.path.join(dest, name))
                    urls.append(f"/api/quantity/crops/{check_id}/{idx}/{name}")
            shutil.rmtree(str(src_dir), ignore_errors=True)
            inp["crops"] = urls
        persisted.append(inp)
    check = QuantityCheck(id=check_id, created_at=now_iso(), inputs=persisted, **data)
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


@router.delete("/checks/{check_id}")
def delete_check(check_id: str, db: Session = Depends(get_db)):
    check = db.get(QuantityCheck, check_id)
    if not check:
        raise HTTPException(404, "not found")
    db.delete(check)
    db.commit()
    shutil.rmtree(os.path.join(app_settings.data_dir, "quantity", check_id), ignore_errors=True)
    return {"deleted": check_id}

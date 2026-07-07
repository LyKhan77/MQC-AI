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
from ..models import Batch, Camera, QuantityCheck
from ..schemas import QuantityCheckIn, QuantityCheckOut, QuantityCheckPatch, QuantityDetectOut
from ..services.crop import crop_objects
from ..services.object_detection import detect, resolve_named_model_path, serialize_detections
from ..services.pipeline import prepare_images
from ..services.quantity import per_class_counts
from ..services.streaming import grab_one
from ..util import gen_id, now_iso
from .settings import get_or_create_setting

router = APIRouter(prefix="/api/quantity", tags=["quantity"])


def parse_classes(value: str | None) -> list[str]:
    out = []
    seen = set()
    for item in (value or "").split(","):
        name = item.strip()
        if name and name not in seen:
            out.append(name)
            seen.add(name)
    return out


def run_quantity_snapshot(frame, setting, model_path, save_frame=False):
    prompts = parse_classes(getattr(setting, "quantity_classes", ""))
    try:
        detections = detect(
            frame,
            setting.quantity_confidence_threshold,
            model_path,
            iou=setting.quantity_nms_iou,
            agnostic_nms=setting.quantity_agnostic_nms,
            prompts=prompts or None,
        )
    except ValueError as exc:
        if str(exc) == "model does not support class prompts":
            raise HTTPException(
                409,
                "selected model does not support class prompts; clear the target classes field",
            ) from exc
        raise

    h, w = frame.shape[:2]
    crop_key = gen_id("qtmp")
    tmp_dir = os.path.join(app_settings.data_dir, "quantity", "_tmp", crop_key)
    files = crop_objects(frame, detections, tmp_dir)
    kept = [d for d in detections if d.x2 > d.x1 and d.y2 > d.y1]
    crops = [
        {
            "file": f,
            "label": kept[i].label if i < len(kept) else "",
            "box": [kept[i].x1, kept[i].y1, kept[i].x2, kept[i].y2] if i < len(kept) else None,
            "url": f"/api/quantity/crops/_tmp/{crop_key}/{f}",
        }
        for i, f in enumerate(files)
    ]
    frame_url = None
    if save_frame:
        os.makedirs(tmp_dir, exist_ok=True)
        cv2.imwrite(os.path.join(tmp_dir, "frame.jpg"), frame)
        frame_url = f"/api/quantity/crops/_tmp/{crop_key}/frame.jpg"
    return {
        "total": len(detections),
        "per_class": per_class_counts(detections),
        "detections": serialize_detections(detections),
        "width": int(w),
        "height": int(h),
        "crop_key": crop_key,
        "crops": crops,
        "frame_url": frame_url,
    }


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
    return run_quantity_snapshot(frame, setting, model_path)


@router.post("/detect/camera/{camera_id}", response_model=QuantityDetectOut)
def detect_quantity_camera(camera_id: str, db: Session = Depends(get_db)):
    cam = db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(404, "camera not found")
    setting = get_or_create_setting(db)
    model_path = resolve_named_model_path(setting.quantity_model)
    if not model_path:
        raise HTTPException(409, "quantity model not configured")
    frame = grab_one(cam.source)
    if frame is None:
        raise HTTPException(503, "camera frame unavailable")
    return run_quantity_snapshot(frame, setting, model_path, save_frame=True)


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


@router.post("/checks/{check_id}/to-qc", status_code=201)
def check_to_qc(check_id: str, db: Session = Depends(get_db)):
    check = db.get(QuantityCheck, check_id)
    if not check:
        raise HTTPException(404, "not found")
    q_dir = os.path.join(app_settings.data_dir, "quantity", check_id)
    if not os.path.isdir(q_dir):
        raise HTTPException(400, "no crops to send")

    batch_id = gen_id("batch")
    dest = os.path.join(app_settings.data_dir, "batches", batch_id)
    os.makedirs(dest, exist_ok=True)
    n = 0
    for sub in sorted(os.listdir(q_dir)):
        subp = os.path.join(q_dir, sub)
        if not os.path.isdir(subp):
            continue
        for filename in sorted(os.listdir(subp)):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                shutil.copy2(
                    os.path.join(subp, filename),
                    os.path.join(dest, f"{sub}_{filename}"),
                )
                n += 1
    if n == 0:
        shutil.rmtree(dest, ignore_errors=True)
        raise HTTPException(400, "no crops to send")

    setting = get_or_create_setting(db)
    batch = Batch(
        id=batch_id,
        name=f"qty_{check_id}",
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


@router.patch("/checks/{check_id}", response_model=QuantityCheckOut)
def patch_check(check_id: str, payload: QuantityCheckPatch, db: Session = Depends(get_db)):
    check = db.get(QuantityCheck, check_id)
    if not check:
        raise HTTPException(404, "not found")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(check, key, value)
    db.commit()
    db.refresh(check)
    return check


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

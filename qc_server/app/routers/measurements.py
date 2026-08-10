import json
import os
import shutil
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..config import settings as app_settings
from ..database import get_db
from ..models import AuditLog, Camera, MeasurementRun
from ..schemas import MeasurementProcessOut, MeasurementRunIn, MeasurementRunOut
from ..services.measurement import (
    calibrate_reference,
    evaluate_item,
    measure_geometry,
    process_image,
)
from ..services.streaming import grab_one
from ..util import gen_id, now_iso

router = APIRouter(prefix="/api/measurements", tags=["measurements"])
_USER = "inspector@gspemail.com"


def _base_dir() -> Path:
    path = Path(app_settings.data_dir, "measurements").resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_owner(owner: str) -> bool:
    return bool(owner) and Path(owner).name == owner and owner not in {".", ".."}


def _file_path(owner: str, filename: str) -> Path:
    if not _safe_owner(owner) or Path(filename).name != filename:
        raise HTTPException(404, "not found")
    path = (_base_dir() / owner / filename).resolve()
    try:
        path.relative_to(_base_dir())
    except ValueError as exc:
        raise HTTPException(404, "not found") from exc
    return path


def _audit(db: Session, action: str, detail: str):
    db.add(AuditLog(
        id=gen_id("log"),
        timestamp=now_iso(),
        user=_USER,
        action=action,
        detail=detail,
    ))


def _json_form(value: str, field: str, default=None):
    try:
        return json.loads(value) if value else (default if default is not None else {})
    except json.JSONDecodeError as exc:
        raise HTTPException(400, f"invalid {field}") from exc


def _calibration_from_payload(payload: dict):
    try:
        point_a = payload["point_a"]
        point_b = payload["point_b"]
        known_mm = payload["known_mm"]
        result = calibrate_reference(point_a, point_b, known_mm)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(400, "invalid calibration") from exc
    return {**result, "point_a": point_a, "point_b": point_b}


def _decode_frame(raw: bytes):
    frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, "invalid image")
    return frame


def _summary(items: list[dict]):
    statuses = [item.get("status", "REVIEW") for item in items]
    if not statuses or "REVIEW" in statuses:
        status = "REVIEW"
    elif "FAIL" in statuses:
        status = "FAIL"
    elif all(value == "PASS" for value in statuses):
        status = "PASS"
    else:
        status = "REVIEW"
    return {
        "status": status,
        "total": len(items),
        "pass": statuses.count("PASS"),
        "fail": statuses.count("FAIL"),
        "review": statuses.count("REVIEW"),
    }


def _evaluate_items(items, calibration):
    result = []
    calibration_valid = bool(calibration.get("valid"))
    for item in items:
        data = item.model_dump() if hasattr(item, "model_dump") else dict(item)
        item_type = data.get("task_type") or data["type"]
        try:
            measured = measure_geometry(item_type, data.get("points", []), calibration, data.get("geometry"))
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(422, f"invalid measurement geometry: {exc}") from exc
        evaluated = evaluate_item(
            measured=measured["value"],
            unit=measured["unit"],
            nominal=data.get("nominal"),
            tolerance=data.get("tolerance"),
            confidence=float(data.get("confidence", 0)),
            calibration_valid=calibration_valid,
            task_type=item_type,
            view_type=data.get("view_type", "top"),
        )
        result.append({
            **data,
            "measured": measured["value"],
            "unit": measured["unit"],
            "pixel_value": measured["pixel_value"],
            **evaluated,
        })
    return result


@router.post("/process", response_model=MeasurementProcessOut)
async def process_measurement(
    file: UploadFile | None = File(default=None),
    camera_id: str | None = Form(default=None),
    source_type: str = Form(default="image"),
    task_type: str = Form(default="linear_dimension"),
    view_type: str = Form(default="top"),
    calibration: str = Form(...),
    options: str = Form(default="{}"),
    db: Session = Depends(get_db),
):
    if file is not None and camera_id:
        raise HTTPException(400, "choose file or camera_id")
    source_camera_id = None
    if file is not None:
        if source_type not in {"image", "mobile_camera"}:
            raise HTTPException(400, "invalid source_type")
        frame = _decode_frame(await file.read())
        source_filename = os.path.basename(file.filename or "capture.png")
    elif camera_id:
        camera = db.get(Camera, camera_id)
        if not camera:
            raise HTTPException(404, "camera not found")
        frame = grab_one(camera.source)
        if frame is None:
            raise HTTPException(503, "camera frame unavailable")
        source_type = "live_camera"
        source_camera_id = camera_id
        source_filename = f"{camera_id}.jpg"
    else:
        raise HTTPException(400, "file or camera_id required")

    calibration_data = _calibration_from_payload(_json_form(calibration, "calibration"))
    options_data = _json_form(options, "options")
    processed = process_image(frame, calibration_data, options_data, task_type=task_type, view_type=view_type)
    key = gen_id("measurement")
    owner = f"tmp-{key}"
    directory = _base_dir() / owner
    directory.mkdir(parents=True, exist_ok=False)
    if not cv2.imwrite(str(directory / "frame.jpg"), frame):
        shutil.rmtree(directory, ignore_errors=True)
        raise HTTPException(500, "could not store frame")
    _audit(db, "MEASUREMENT_PROCESSED", f"{source_type}:{source_filename}")
    db.commit()
    return {
        "source_key": owner,
        "source_type": source_type,
        "source_filename": source_filename,
        "source_camera_id": source_camera_id,
        "frame_url": f"/api/measurements/files/{owner}/frame.jpg",
        "width": int(frame.shape[1]),
        "height": int(frame.shape[0]),
        "calibration": calibration_data,
        **processed,
    }


@router.get("/files/{owner}/{filename}")
def serve_measurement_file(owner: str, filename: str):
    path = _file_path(owner, filename)
    if not path.is_file():
        raise HTTPException(404, "not found")
    return FileResponse(path)


@router.post("", response_model=MeasurementRunOut, status_code=201)
def save_measurement(payload: MeasurementRunIn, db: Session = Depends(get_db)):
    owner = payload.source_key
    source_dir = _base_dir() / owner
    source = _file_path(owner, "frame.jpg")
    if not owner.startswith("tmp-") or not source.is_file() or not source_dir.is_dir():
        raise HTTPException(400, "measurement source not found")
    calibration = payload.calibration
    items = _evaluate_items(payload.items, calibration)
    run_id = gen_id("measurement")
    destination = _base_dir() / run_id
    image = cv2.imread(str(source))
    if image is None:
        raise HTTPException(400, "invalid measurement frame")
    try:
        source_dir.rename(destination)
        run = MeasurementRun(
            id=run_id,
            created_at=now_iso(),
            name=payload.name.strip(),
            source_type=payload.source_type,
            source_filename=payload.source_filename,
            source_camera_id=payload.source_camera_id,
            file_path=str(destination / "frame.jpg"),
            source_url=f"/api/measurements/files/{run_id}/frame.jpg",
            width=int(image.shape[1]),
            height=int(image.shape[0]),
            calibration=calibration,
            processing={
                "engine": "opencv",
                "candidate_methods": ["lsd", "hough"],
                "hole_methods": ["hough_circle_alt", "fit_ellipse"],
                "task_type": payload.task_type,
                "view_type": payload.view_type,
            },
            items=items,
            summary=_summary(items),
        )
        db.add(run)
        _audit(db, "MEASUREMENT_EVALUATED", f"{run_id}:{run.summary['status']}")
        _audit(db, "MEASUREMENT_SAVED", run_id)
        db.commit()
        db.refresh(run)
        return run
    except Exception:
        db.rollback()
        if destination.is_dir() and not source_dir.exists():
            destination.rename(source_dir)
        raise


@router.get("", response_model=list[MeasurementRunOut])
def list_measurements(db: Session = Depends(get_db)):
    return db.query(MeasurementRun).order_by(desc(MeasurementRun.created_at)).all()


@router.get("/{run_id}", response_model=MeasurementRunOut)
def get_measurement(run_id: str, db: Session = Depends(get_db)):
    run = db.get(MeasurementRun, run_id)
    if not run:
        raise HTTPException(404, "not found")
    return run


@router.delete("/{run_id}")
def delete_measurement(run_id: str, db: Session = Depends(get_db)):
    run = db.get(MeasurementRun, run_id)
    if not run:
        raise HTTPException(404, "not found")
    file_path = Path(run.file_path).parent
    db.delete(run)
    _audit(db, "MEASUREMENT_DELETED", run_id)
    db.commit()
    shutil.rmtree(file_path, ignore_errors=True)
    return {"deleted": run_id}

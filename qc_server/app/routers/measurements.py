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
from ..models import AuditLog, Camera, MeasurementProfile, MeasurementRun, MeasurementSession
from ..schemas import (
    MeasurementCaptureOut,
    MeasurementProcessOut,
    MeasurementProfileIn,
    MeasurementProfileOut,
    MeasurementProfilePatch,
    MeasurementRunIn,
    MeasurementRunOut,
    MeasurementSessionCreate,
    MeasurementSessionOut,
    MeasurementSessionPatch,
)
from ..services.measurement import (
    calibrate_reference,
    evaluate_item,
    measure_geometry,
    pose_task_supported,
    process_image,
    task_view_supported,
    validate_measurement_profile,
)
from ..services.streaming import grab_one
from ..util import gen_id, now_iso

router = APIRouter(prefix="/api/measurements", tags=["measurements"])
meta_router = APIRouter(prefix="/api", tags=["measurements"])
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


def _validate_profile_payload(payload: dict):
    if payload.get("scale_type") not in {"GLOBAL", "DETAIL"}:
        raise HTTPException(400, "invalid scale_type")
    if payload.get("status") not in {"draft", "valid", "approved", "invalid"}:
        raise HTTPException(400, "invalid profile status")
    capability = payload.get("capability") or {}
    try:
        minimum = float(capability.get("minimum_supported_feature_mm", 0))
        maximum = float(capability.get("maximum_supported_span_mm", 0))
    except (TypeError, ValueError) as exc:
        raise HTTPException(400, "invalid profile capability") from exc
    if minimum < 0 or maximum < 0 or (maximum and minimum > maximum):
        raise HTTPException(400, "invalid profile capability")


@meta_router.post("/measurement-profiles", response_model=MeasurementProfileOut, status_code=201)
def create_measurement_profile(payload: MeasurementProfileIn, db: Session = Depends(get_db)):
    data = payload.model_dump()
    _validate_profile_payload(data)
    profile = MeasurementProfile(id=gen_id("profile"), **data)
    db.add(profile)
    _audit(db, "MEASUREMENT_PROFILE_CREATED", profile.id)
    db.commit()
    db.refresh(profile)
    return profile


@meta_router.get("/measurement-profiles", response_model=list[MeasurementProfileOut])
def list_measurement_profiles(db: Session = Depends(get_db)):
    return db.query(MeasurementProfile).order_by(MeasurementProfile.name).all()


@meta_router.get("/measurement-profiles/{profile_id}", response_model=MeasurementProfileOut)
def get_measurement_profile(profile_id: str, db: Session = Depends(get_db)):
    profile = db.get(MeasurementProfile, profile_id)
    if not profile:
        raise HTTPException(404, "not found")
    return profile


@meta_router.patch("/measurement-profiles/{profile_id}", response_model=MeasurementProfileOut)
def update_measurement_profile(
    profile_id: str,
    payload: MeasurementProfilePatch,
    db: Session = Depends(get_db),
):
    profile = db.get(MeasurementProfile, profile_id)
    if not profile:
        raise HTTPException(404, "not found")
    data = {key: value for key, value in payload.model_dump().items() if value is not None}
    candidate = {
        "scale_type": data.get("scale_type", profile.scale_type),
        "status": data.get("status", profile.status),
        "capability": data.get("capability", profile.capability),
    }
    _validate_profile_payload(candidate)
    for key, value in data.items():
        setattr(profile, key, value)
    _audit(db, "MEASUREMENT_PROFILE_UPDATED", profile.id)
    db.commit()
    db.refresh(profile)
    return profile


@meta_router.delete("/measurement-profiles/{profile_id}")
def delete_measurement_profile(profile_id: str, db: Session = Depends(get_db)):
    profile = db.get(MeasurementProfile, profile_id)
    if not profile:
        raise HTTPException(404, "not found")
    db.delete(profile)
    _audit(db, "MEASUREMENT_PROFILE_DELETED", profile_id)
    db.commit()
    return {"deleted": profile_id}


def _session_summary(session: MeasurementSession, db: Session):
    views = db.query(MeasurementRun).filter(MeasurementRun.session_id == session.id).all()
    statuses = [view.summary.get("status", "REVIEW") for view in views]
    if not statuses:
        status = "IN_PROGRESS"
    elif "FAIL" in statuses:
        status = "FAIL"
    elif "REVIEW" in statuses:
        status = "REVIEW"
    elif all(value == "PASS" for value in statuses):
        status = "PASS"
    else:
        status = "REVIEW"
    return {
        "status": status,
        "view_count": len(views),
        "pass": statuses.count("PASS"),
        "fail": statuses.count("FAIL"),
        "review": statuses.count("REVIEW"),
    }


def _session_payload(session: MeasurementSession, db: Session):
    views = db.query(MeasurementRun).filter(
        MeasurementRun.session_id == session.id,
    ).order_by(MeasurementRun.created_at).all()
    session.summary = _session_summary(session, db)
    return {
        "id": session.id,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "name": session.name,
        "status": session.status,
        "summary": session.summary,
        "views": views,
    }


@meta_router.post("/measurement-sessions", response_model=MeasurementSessionOut, status_code=201)
def create_measurement_session(
    payload: MeasurementSessionCreate,
    db: Session = Depends(get_db),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(400, "session name required")
    timestamp = now_iso()
    session = MeasurementSession(
        id=gen_id("session"),
        created_at=timestamp,
        updated_at=timestamp,
        name=name,
        summary={"status": "IN_PROGRESS", "view_count": 0, "pass": 0, "fail": 0, "review": 0},
    )
    db.add(session)
    _audit(db, "MEASUREMENT_SESSION_CREATED", session.id)
    db.commit()
    db.refresh(session)
    return _session_payload(session, db)


@meta_router.get("/measurement-sessions", response_model=list[MeasurementSessionOut])
def list_measurement_sessions(db: Session = Depends(get_db)):
    sessions = db.query(MeasurementSession).order_by(desc(MeasurementSession.created_at)).all()
    return [_session_payload(session, db) for session in sessions]


@meta_router.get("/measurement-sessions/{session_id}", response_model=MeasurementSessionOut)
def get_measurement_session(session_id: str, db: Session = Depends(get_db)):
    session = db.get(MeasurementSession, session_id)
    if not session:
        raise HTTPException(404, "not found")
    return _session_payload(session, db)


def _persist_measurement_view(db: Session, payload: MeasurementRunIn, session_id: str | None = None):
    owner = payload.source_key
    source_dir = _base_dir() / owner
    source = _file_path(owner, "frame.jpg")
    if not owner.startswith("tmp-") or not source.is_file() or not source_dir.is_dir():
        raise HTTPException(400, "measurement source not found")
    items = _evaluate_items(payload.items, payload.calibration)
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
            session_id=session_id or payload.session_id,
            view_label=payload.view_label,
            pose_type=payload.pose_type,
            scale_profile_id=payload.scale_profile_id,
            view_status="saved",
            calibration=payload.calibration,
            processing={
                "engine": "opencv",
                "candidate_methods": ["lsd", "hough"],
                "hole_methods": ["hough_circle_alt", "fit_ellipse"],
                "task_type": payload.task_type,
                "view_type": payload.view_type,
                "pose_type": payload.pose_type,
                "scale_profile_id": payload.scale_profile_id,
            },
            items=items,
            summary=_summary(items),
        )
        db.add(run)
        return run, destination, source_dir
    except Exception:
        if destination.is_dir() and not source_dir.exists():
            destination.rename(source_dir)
        raise


@meta_router.post(
    "/measurement-sessions/{session_id}/views",
    response_model=MeasurementRunOut,
    status_code=201,
)
def save_measurement_session_view(
    session_id: str,
    payload: MeasurementRunIn,
    db: Session = Depends(get_db),
):
    session = db.get(MeasurementSession, session_id)
    if not session:
        raise HTTPException(404, "not found")
    if session.status != "in_progress":
        raise HTTPException(409, "session is not editable")
    run, _, _ = _persist_measurement_view(db, payload, session_id)
    session.updated_at = now_iso()
    session.summary = _session_summary(session, db)
    _audit(db, "MEASUREMENT_VIEW_SAVED", f"{session_id}:{run.id}")
    db.commit()
    db.refresh(run)
    return run


@meta_router.delete("/measurement-sessions/{session_id}/views/{view_id}")
def delete_measurement_session_view(
    session_id: str,
    view_id: str,
    db: Session = Depends(get_db),
):
    session = db.get(MeasurementSession, session_id)
    run = db.get(MeasurementRun, view_id)
    if not session or not run or run.session_id != session_id:
        raise HTTPException(404, "not found")
    directory = Path(run.file_path).parent
    db.delete(run)
    session.updated_at = now_iso()
    _audit(db, "MEASUREMENT_VIEW_DELETED", f"{session_id}:{view_id}")
    db.commit()
    shutil.rmtree(directory, ignore_errors=True)
    return {"deleted": view_id}


@meta_router.patch("/measurement-sessions/{session_id}", response_model=MeasurementSessionOut)
def update_measurement_session(
    session_id: str,
    payload: MeasurementSessionPatch,
    db: Session = Depends(get_db),
):
    session = db.get(MeasurementSession, session_id)
    if not session:
        raise HTTPException(404, "not found")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data:
        name = str(data["name"]).strip()
        if not name:
            raise HTTPException(400, "session name required")
        session.name = name
    if "status" in data:
        status = data["status"]
        if status not in {"in_progress", "complete", "cancelled"}:
            raise HTTPException(400, "invalid session status")
        if status == "complete":
            views = db.query(MeasurementRun).filter(MeasurementRun.session_id == session_id).count()
            if not views:
                raise HTTPException(409, "session has no saved views")
            _audit(db, "MEASUREMENT_SESSION_COMPLETED", session_id)
        session.status = status
    session.updated_at = now_iso()
    session.summary = _session_summary(session, db)
    db.commit()
    db.refresh(session)
    return _session_payload(session, db)


@meta_router.delete("/measurement-sessions/{session_id}")
def delete_measurement_session(session_id: str, db: Session = Depends(get_db)):
    session = db.get(MeasurementSession, session_id)
    if not session:
        raise HTTPException(404, "not found")
    views = db.query(MeasurementRun).filter(MeasurementRun.session_id == session_id).all()
    directories = [Path(view.file_path).parent for view in views]
    for view in views:
        db.delete(view)
    db.delete(session)
    _audit(db, "MEASUREMENT_SESSION_DELETED", session_id)
    db.commit()
    for directory in directories:
        shutil.rmtree(directory, ignore_errors=True)
    return {"deleted": session_id}


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


@router.post("/capture", response_model=MeasurementCaptureOut)
def capture_measurement(
    camera_id: str = Form(...),
    db: Session = Depends(get_db),
):
    camera = db.get(Camera, camera_id)
    if not camera:
        raise HTTPException(404, "camera not found")
    frame = grab_one(camera.source)
    if frame is None:
        raise HTTPException(503, "camera frame unavailable")
    owner = f"tmp-{gen_id('measurement')}"
    directory = _base_dir() / owner
    directory.mkdir(parents=True, exist_ok=False)
    if not cv2.imwrite(str(directory / "frame.jpg"), frame):
        shutil.rmtree(directory, ignore_errors=True)
        raise HTTPException(500, "could not store frame")
    source_filename = f"{camera_id}.jpg"
    _audit(db, "MEASUREMENT_CAPTURED", f"live_camera:{source_filename}")
    db.commit()
    return {
        "source_key": owner,
        "source_type": "live_camera",
        "source_filename": source_filename,
        "source_camera_id": camera_id,
        "frame_url": f"/api/measurements/files/{owner}/frame.jpg",
        "width": int(frame.shape[1]),
        "height": int(frame.shape[0]),
    }


@router.post("/process", response_model=MeasurementProcessOut)
async def process_measurement(
    file: UploadFile | None = File(default=None),
    camera_id: str | None = Form(default=None),
    source_key: str | None = Form(default=None),
    source_filename: str | None = Form(default=None),
    source_camera_id: str | None = Form(default=None),
    source_type: str = Form(default="image"),
    task_type: str = Form(default="linear_dimension"),
    view_type: str = Form(default="top"),
    view_label: str = Form(default=""),
    pose_type: str = Form(default="TOP_FACE"),
    profile_id: str | None = Form(default=None),
    scale_profile_id: str | None = Form(default=None),
    calibration: str = Form(...),
    options: str = Form(default="{}"),
    db: Session = Depends(get_db),
):
    if sum(value is not None for value in (file, camera_id, source_key)) > 1:
        raise HTTPException(400, "choose one measurement source")
    if source_key:
        if source_type != "live_camera":
            raise HTTPException(400, "invalid source_type")
        if not source_key.startswith("tmp-"):
            raise HTTPException(400, "invalid source_key")
        source_path = _file_path(source_key, "frame.jpg")
        frame = cv2.imread(str(source_path))
        if frame is None:
            raise HTTPException(400, "invalid measurement frame")
        source_filename = source_filename or f"{source_key}.jpg"
    elif file is not None:
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

    profile_id = profile_id or scale_profile_id
    profile = None
    profile_validation = {"valid": True, "reason": ""}
    if profile_id:
        profile = db.get(MeasurementProfile, profile_id)
        if not profile:
            raise HTTPException(404, "measurement profile not found")
        profile_validation = validate_measurement_profile(
            {
                "id": profile.id,
                "status": profile.status,
                "camera_id": profile.camera_id,
                "resolution_width": profile.resolution_width,
                "resolution_height": profile.resolution_height,
                "calibration": profile.calibration,
            },
            int(frame.shape[1]),
            int(frame.shape[0]),
            source_camera_id,
        )
    calibration_data = _calibration_from_payload(_json_form(calibration, "calibration"))
    if profile_validation["valid"] and profile:
        calibration_data = profile.calibration
    options_data = _json_form(options, "options")
    if not task_view_supported(task_type, view_type):
        processed = {"readiness": "review", "reason": "unsupported_view", "candidates": [], "holes": []}
    elif not pose_task_supported(task_type, pose_type):
        processed = {"readiness": "review", "reason": "unsupported_pose", "candidates": [], "holes": []}
    elif not profile_validation["valid"]:
        processed = {
            "readiness": "review",
            "reason": profile_validation["reason"],
            "candidates": [],
            "holes": [],
        }
    else:
        processed = process_image(frame, calibration_data, options_data, task_type=task_type, view_type=view_type)
    owner = source_key or f"tmp-{gen_id('measurement')}"
    directory = _base_dir() / owner
    if source_key:
        if not directory.is_dir() or not (directory / "frame.jpg").is_file():
            raise HTTPException(400, "measurement source not found")
    else:
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
        "view_label": view_label,
        "pose_type": pose_type,
        "scale_profile_id": profile_id,
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

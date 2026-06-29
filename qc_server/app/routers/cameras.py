import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from ..config import settings as app_settings
from ..database import get_db
from ..models import Camera
from ..schemas import CameraIn, CameraOut
from ..services.annotated_stream import annotated_mjpeg, downscale
from ..services.crop_session import get_session, reset_session
from ..services.frame_grabber import FrameGrabber
from ..services.object_detection import detect, resolve_model_path
from ..services.presence_counter import PresenceCounter
from ..services.streaming import grab_one, mjpeg_frames
from .settings import get_or_create_setting

router = APIRouter(prefix="/api/cameras", tags=["cameras"])
_latest_stats: dict[str, dict] = {}


@router.get("", response_model=list[CameraOut])
def list_cameras(db: Session = Depends(get_db)):
    return db.query(Camera).all()


@router.post("", response_model=CameraOut, status_code=201)
def create_camera(payload: CameraIn, db: Session = Depends(get_db)):
    if db.get(Camera, payload.id):
        raise HTTPException(409, "camera id already exists")
    cam = Camera(**payload.model_dump())
    db.add(cam)
    db.commit()
    db.refresh(cam)
    return cam


@router.patch("/{camera_id}", response_model=CameraOut)
def patch_camera(camera_id: str, payload: dict, db: Session = Depends(get_db)):
    cam = db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(404, "camera not found")
    for key, value in payload.items():
        if hasattr(cam, key) and key != "id":
            setattr(cam, key, value)
    db.commit()
    db.refresh(cam)
    return cam


@router.delete("/{camera_id}")
def delete_camera(camera_id: str, db: Session = Depends(get_db)):
    cam = db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(404, "camera not found")
    db.delete(cam)
    db.commit()
    return {"deleted": camera_id}


@router.get("/{camera_id}/stream")
def stream_camera(camera_id: str, db: Session = Depends(get_db)):
    cam = db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(404, "camera not found")
    return StreamingResponse(
        mjpeg_frames(cam.source),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/{camera_id}/detect-stream")
def detect_stream(camera_id: str, db: Session = Depends(get_db)):
    cam = db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(404, "camera not found")
    setting = get_or_create_setting(db)
    model_path = resolve_model_path(setting)
    if not model_path:
        raise HTTPException(409, "model not configured")

    grabber = FrameGrabber(cam.source).start()
    session = get_session(camera_id)
    counter = PresenceCounter(session)

    def on_stats(count, fps):
        _latest_stats[camera_id] = {"count": count, "fps": fps}

    def stream():
        try:
            yield from annotated_mjpeg(
                grabber,
                cam.count_mode,
                setting.confidence_threshold,
                model_path,
                on_stats,
                app_settings.stream_max_width,
                app_settings.stream_max_fps,
                counter=counter.update,
            )
        finally:
            grabber.stop()

    return StreamingResponse(
        stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/{camera_id}/count")
def camera_count(camera_id: str):
    return _latest_stats.get(camera_id, {"count": 0, "fps": 0})


@router.post("/{camera_id}/crop-session/finalize")
def finalize_crop_session(camera_id: str, db: Session = Depends(get_db)):
    if not db.get(Camera, camera_id):
        raise HTTPException(404, "camera not found")
    result = get_session(camera_id).finalize()
    ts = result["session_ts"]
    urls = [
        f"/api/cameras/{camera_id}/crops/{ts}/{f}"
        for f in result["files"]
    ]
    return {"count": result["count"], "folder": result["folder"], "crop_urls": urls}


@router.post("/{camera_id}/crop-session/start")
def start_crop_session(camera_id: str, db: Session = Depends(get_db)):
    if not db.get(Camera, camera_id):
        raise HTTPException(404, "camera not found")
    session = reset_session(camera_id)
    return {"session_ts": session.session_ts}


@router.post("/{camera_id}/capture")
def capture(camera_id: str, db: Session = Depends(get_db)):
    cam = db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(404, "camera not found")
    setting = get_or_create_setting(db)
    model_path = resolve_model_path(setting)
    if not model_path:
        raise HTTPException(409, "model not configured")

    frame = grab_one(cam.source)
    if frame is None:
        raise HTTPException(503, "camera frame unavailable")

    small = downscale(frame, app_settings.stream_max_width)
    scale = frame.shape[1] / small.shape[1] if small.shape[1] else 1.0
    detections = detect(small, setting.confidence_threshold, model_path)

    session = get_session(camera_id)
    written = session.add_captured(frame, detections, scale)
    result = session.finalize()
    ts = result["session_ts"]
    urls = [f"/api/cameras/{camera_id}/crops/{ts}/{f}" for f in result["files"]]
    return {"captured": len(written), "total_count": result["count"], "crop_urls": urls}


@router.post("/{camera_id}/crop-session/approve")
def approve_crops(camera_id: str, payload: dict, db: Session = Depends(get_db)):
    if not db.get(Camera, camera_id):
        raise HTTPException(404, "camera not found")
    files = payload.get("files", [])
    folder = get_session(camera_id).approve(files)
    if not folder:
        raise HTTPException(400, "no crops approved")
    from ..storage import list_images
    return {"folder": folder, "count": len(list_images(folder))}


@router.get("/{camera_id}/crops/{session_ts}/{filename}")
def serve_crop(camera_id: str, session_ts: str, filename: str):
    path = os.path.join(
        app_settings.data_dir, "crops", camera_id, session_ts, filename
    )
    if not os.path.isfile(path):
        raise HTTPException(404, "crop not found")
    return FileResponse(path, media_type="image/jpeg")

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Camera
from ..schemas import CameraIn, CameraOut
from ..services.annotated_stream import annotated_mjpeg
from ..services.frame_grabber import FrameGrabber
from ..services.object_detection import resolve_model_path
from ..services.streaming import mjpeg_frames
from .settings import get_or_create_setting

router = APIRouter(prefix="/api/cameras", tags=["cameras"])
_latest_count: dict[str, int] = {}


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

    def on_count(count):
        _latest_count[camera_id] = count

    def stream():
        try:
            yield from annotated_mjpeg(
                grabber,
                cam.count_mode,
                setting.confidence_threshold,
                model_path,
                on_count,
            )
        finally:
            grabber.stop()

    return StreamingResponse(
        stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/{camera_id}/count")
def camera_count(camera_id: str):
    return {"count": _latest_count.get(camera_id, 0)}

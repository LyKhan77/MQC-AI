from fastapi import APIRouter, Depends, HTTPException, WebSocket
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.websockets import WebSocketDisconnect

from ..database import SessionLocal
from ..database import get_db
from ..models import Camera
from ..schemas import CameraIn, CameraOut
from ..services.detect_stream import detection_messages
from ..services.object_detection import resolve_model_path
from ..services.streaming import mjpeg_frames
from .settings import get_or_create_setting

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


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


@router.websocket("/{camera_id}/detect")
async def detect_ws(websocket: WebSocket, camera_id: str):
    await websocket.accept()
    db = SessionLocal()
    try:
        cam = db.get(Camera, camera_id)
        if not cam:
            await websocket.close(code=1011, reason="camera not found")
            return
        setting = get_or_create_setting(db)
        model_path = resolve_model_path(setting)
        if not model_path:
            await websocket.close(code=1011, reason="model not configured")
            return
        # Run the blocking capture+inference generator in a threadpool so the
        # event loop stays responsive (otherwise the websockets keepalive/close
        # races with our send and raises AssertionError in _drain_helper).
        gen = detection_messages(cam, setting.confidence_threshold, model_path)
        try:
            while True:
                message = await run_in_threadpool(lambda: next(gen, None))
                if message is None:
                    break
                await websocket.send_json(message)
        finally:
            closer = getattr(gen, "close", None)
            if closer is not None:
                closer()  # release the camera promptly on disconnect/end
    except WebSocketDisconnect:
        pass
    finally:
        db.close()

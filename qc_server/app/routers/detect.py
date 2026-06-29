import base64
import os
import uuid

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..config import settings as app_settings
from ..database import get_db
from ..services.annotated_stream import annotate, annotated_mjpeg
from ..services.frame_grabber import FrameGrabber
from ..services.object_detection import detect, resolve_model_path, serialize_detections
from .settings import get_or_create_setting

router = APIRouter(prefix="/api/detect", tags=["detect"])
_videos: dict[str, str] = {}


@router.post("/image")
async def detect_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    setting = get_or_create_setting(db)
    model_path = resolve_model_path(setting)
    if not model_path:
        raise HTTPException(409, "model not configured")

    raw = await file.read()
    frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, "invalid image")

    detections = detect(frame, setting.confidence_threshold, model_path)
    annotate(frame, detections, len(detections))
    ok, buf = cv2.imencode(".jpg", frame)
    if not ok:
        raise HTTPException(400, "invalid image")

    return {
        "image": base64.b64encode(buf.tobytes()).decode("ascii"),
        "detections": serialize_detections(detections),
        "count": len(detections),
    }


@router.post("/video")
async def upload_video(file: UploadFile = File(...)):
    folder = os.path.join(app_settings.data_dir, "uploads")
    os.makedirs(folder, exist_ok=True)
    video_id = uuid.uuid4().hex[:8]
    path = os.path.join(folder, f"{video_id}_{os.path.basename(file.filename or 'video')}")
    with open(path, "wb") as fh:
        fh.write(await file.read())
    _videos[video_id] = path
    return {"video_id": video_id}


@router.get("/video/{video_id}/stream")
def video_stream(video_id: str, db: Session = Depends(get_db)):
    path = _videos.get(video_id)
    if not path or not os.path.isfile(path):
        raise HTTPException(404, "video not found")
    setting = get_or_create_setting(db)
    model_path = resolve_model_path(setting)
    if not model_path:
        raise HTTPException(409, "model not configured")

    grabber = FrameGrabber(path).start()

    def stream():
        try:
            yield from annotated_mjpeg(
                grabber,
                "single",
                setting.confidence_threshold,
                model_path,
                lambda count, fps: None,
                app_settings.stream_max_width,
                app_settings.stream_max_fps,
            )
        finally:
            grabber.stop()

    return StreamingResponse(stream(), media_type="multipart/x-mixed-replace; boundary=frame")

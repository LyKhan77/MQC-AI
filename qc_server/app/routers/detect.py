import base64
import os
import uuid

import cv2
import numpy as np
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from ..config import settings as app_settings
from ..database import get_db
from ..services import detect_extract, job_queue
from ..services.annotated_stream import annotate, annotated_mjpeg
from ..services.crop_session import approve_session, crop_file_path, get_session, reset_session
from ..services.frame_grabber import FrameGrabber
from ..services.object_detection import detect, resolve_model_path, serialize_detections
from ..util import gen_id
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


@router.post("/image/process")
async def process_image(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    setting = get_or_create_setting(db)
    model_path = resolve_model_path(setting)
    if not model_path:
        raise HTTPException(409, "model not configured")

    key = gen_id("media")
    session = reset_session(key)
    valid_count = 0
    for file in files:
        raw = await file.read()
        frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            continue
        detections = detect(frame, setting.confidence_threshold, model_path)
        session.add_captured(frame, detections, 1.0)
        valid_count += 1
    if valid_count == 0:
        raise HTTPException(400, "no valid images")

    result = session.finalize()
    urls = [f"/api/detect/crops/{key}/{result['session_ts']}/{f}" for f in result["files"]]
    return {"key": key, "count": result["count"], "crop_urls": urls}


@router.post("/video/{video_id}/extract")
def extract_video(video_id: str, background: BackgroundTasks, db: Session = Depends(get_db)):
    path = _videos.get(video_id)
    if not path or not os.path.isfile(path):
        raise HTTPException(404, "video not found")
    setting = get_or_create_setting(db)
    model_path = resolve_model_path(setting)
    if not model_path:
        raise HTTPException(409, "model not configured")
    detect_extract.start(video_id)
    background.add_task(
        detect_extract.run_video_extract,
        video_id,
        path,
        setting.confidence_threshold,
        model_path,
        app_settings.stream_max_width,
    )
    return {"video_id": video_id, "status": "processing"}


@router.get("/video/{video_id}/extract/status")
def extract_status(video_id: str):
    st = detect_extract.status(video_id)
    return {**st, "progress": job_queue.get(video_id)}


@router.get("/crop-session/{key}")
def crop_session_list(key: str):
    result = get_session(key).finalize()
    ts = result["session_ts"]
    urls = [f"/api/detect/crops/{key}/{ts}/{f}" for f in result["files"]]
    return {"count": result["count"], "crop_urls": urls}


@router.post("/crop-session/{key}/approve")
def approve_crop_session(key: str, payload: dict):
    folder = approve_session(key, payload.get("files", []))
    if not folder:
        raise HTTPException(400, "no crops approved")
    from ..storage import list_images
    return {"folder": folder, "count": len(list_images(folder))}


@router.get("/crops/{key}/{session_ts}/{filename}")
def serve_media_crop(key: str, session_ts: str, filename: str):
    path = crop_file_path(key, session_ts, filename)
    if not os.path.isfile(path):
        raise HTTPException(404, "crop not found")
    return FileResponse(path)

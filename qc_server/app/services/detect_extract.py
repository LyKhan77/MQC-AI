from threading import Lock

import cv2

from . import job_queue
from .annotated_stream import downscale
from .crop_session import reset_session
from .object_detection import detect
from .presence_counter import PresenceCounter

_status: dict[str, dict] = {}
_lock = Lock()


def start(video_id):
    with _lock:
        _status[video_id] = {"status": "processing", "count": 0}
    job_queue.set_total(video_id, 0)


def status(video_id):
    with _lock:
        return dict(_status.get(video_id, {"status": "idle", "count": 0}))


def run_video_extract(video_id, path, conf_threshold, model_path, max_width, capture_factory=cv2.VideoCapture):
    session = reset_session(video_id)
    counter = PresenceCounter(session)
    cap = capture_factory(path)
    try:
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        job_queue.set_total(video_id, total)
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            small = downscale(frame, max_width)
            scale = frame.shape[1] / small.shape[1] if small.shape[1] else 1.0
            detections = detect(small, conf_threshold, model_path)
            counter.update(frame, detections, scale)
            job_queue.increment(video_id)
        result = session.finalize()
        with _lock:
            _status[video_id] = {"status": "done", "count": result["count"]}
    except Exception as exc:  # noqa: BLE001
        with _lock:
            _status[video_id] = {"status": "failed", "count": 0, "error": str(exc)}
        raise
    finally:
        cap.release()

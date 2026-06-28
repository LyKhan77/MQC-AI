import base64

import cv2

from .counting import count_single, update_tracking
from .inference import detect, serialize_detections
from .streaming import open_capture


def detection_messages(camera, conf_threshold):
    if not camera.source:
        return
    cap = open_capture(camera.source)
    try:
        if not cap.isOpened():
            return
        tracker = None
        seen_ids = set()
        if camera.count_mode == "tracking":
            import supervision as sv  # lazy, server-only

            tracker = sv.ByteTrack()
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            detections = detect(frame, conf_threshold)
            if tracker is not None:
                detections = _apply_tracker(tracker, detections)
                count = update_tracking(seen_ids, detections)
            else:
                count = count_single(detections)
            ok, buf = cv2.imencode(".jpg", frame)
            if not ok:
                continue
            yield {
                "frame": base64.b64encode(buf.tobytes()).decode("ascii"),
                "detections": serialize_detections(detections),
                "count": count,
            }
    finally:
        cap.release()


def _apply_tracker(tracker, detections):
    # Smoke-verified on GPU server against installed supervision version.
    import numpy as np
    import supervision as sv

    if not detections:
        return detections
    xyxy = np.array([[d.x1, d.y1, d.x2, d.y2] for d in detections], dtype=float)
    conf = np.array([d.confidence for d in detections], dtype=float)
    class_id = np.zeros(len(detections), dtype=int)
    sv_det = sv.Detections(xyxy=xyxy, confidence=conf, class_id=class_id)
    tracked = tracker.update_with_detections(sv_det)
    for i in range(len(tracked)):
        detections[i].track_id = int(tracked.tracker_id[i]) if tracked.tracker_id is not None else None
    return detections

import time

import cv2

from .counting import count_single, update_tracking
from .object_detection import detect

_BOX = (72, 161, 36)


def annotate(frame, detections, count):
    for d in detections:
        cv2.rectangle(frame, (d.x1, d.y1), (d.x2, d.y2), _BOX, 2)
        cv2.putText(
            frame,
            f"{d.label} {d.confidence * 100:.0f}%",
            (d.x1, max(12, d.y1 - 4)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            _BOX,
            1,
        )
    cv2.putText(
        frame,
        f"count: {count}",
        (8, 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )
    return frame


def annotated_mjpeg(grabber, count_mode, conf_threshold, model_path, on_count):
    tracker = None
    seen_ids = set()
    if count_mode == "tracking":
        import supervision as sv  # lazy, server-only

        tracker = sv.ByteTrack()

    while True:
        frame = grabber.read()
        if frame is None:
            if grabber.finished():
                break
            time.sleep(0.03)
            continue

        detections = detect(frame, conf_threshold, model_path)
        if tracker is not None:
            from .detect_tracker import apply_tracker

            detections = apply_tracker(tracker, detections)
            count = update_tracking(seen_ids, detections)
        else:
            count = count_single(detections)

        annotate(frame, detections, count)
        on_count(count)
        ok, buf = cv2.imencode(".jpg", frame)
        if not ok:
            continue
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"

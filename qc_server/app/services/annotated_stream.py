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


def downscale(frame, max_width):
    if not max_width:
        return frame
    h, w = frame.shape[:2]
    if w <= max_width:
        return frame
    scale = max_width / w
    return cv2.resize(frame, (max_width, int(h * scale)))


def annotated_mjpeg(
    grabber,
    count_mode,
    conf_threshold,
    model_path,
    on_stats,
    max_width=960,
    max_fps=15,
):
    tracker = None
    seen_ids = set()
    if count_mode == "tracking":
        import supervision as sv  # lazy, server-only

        tracker = sv.ByteTrack()

    min_interval = 1.0 / max_fps if max_fps else 0.0
    last = None
    fps = 0.0

    while True:
        frame = grabber.read()
        if frame is None:
            if grabber.finished():
                break
            time.sleep(0.03)
            continue

        frame = downscale(frame, max_width)
        detections = detect(frame, conf_threshold, model_path)
        if tracker is not None:
            from .detect_tracker import apply_tracker

            detections = apply_tracker(tracker, detections)
            count = update_tracking(seen_ids, detections)
        else:
            count = count_single(detections)

        annotate(frame, detections, count)

        now = time.monotonic()
        if last is not None and now > last:
            inst = 1.0 / (now - last)
            fps = inst if fps == 0.0 else (0.8 * fps + 0.2 * inst)
        last = now
        on_stats(count, round(fps, 1))

        ok, buf = cv2.imencode(".jpg", frame)
        if not ok:
            continue
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"

        if min_interval:
            remaining = min_interval - (time.monotonic() - now)
            if remaining > 0:
                time.sleep(remaining)

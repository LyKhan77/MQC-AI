import cv2

_BOUNDARY = b"--frame"


def open_capture(source):
    return cv2.VideoCapture(source)


def probe(source) -> bool:
    cap = open_capture(source)
    try:
        if not cap.isOpened():
            return False
        ok, _ = cap.read()
        return bool(ok)
    finally:
        cap.release()


def mjpeg_frames(source):
    cap = open_capture(source)
    try:
        if not cap.isOpened():
            return
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            ok, buf = cv2.imencode(".jpg", frame)
            if not ok:
                continue
            yield (
                _BOUNDARY
                + b"\r\nContent-Type: image/jpeg\r\n\r\n"
                + buf.tobytes()
                + b"\r\n"
            )
    finally:
        cap.release()

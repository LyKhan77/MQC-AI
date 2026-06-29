import importlib

import cv2
import numpy as np
import pytest

from app.services.object_detection import Detection


def _detect_router():
    try:
        return importlib.import_module("app.routers.detect")
    except ModuleNotFoundError:
        pytest.fail("app.routers.detect missing")


def _png_bytes():
    ok, buf = cv2.imencode(".png", np.zeros((20, 20, 3), dtype=np.uint8))
    assert ok
    return buf.tobytes()


def test_detect_image_returns_annotated(client, monkeypatch):
    detect_router = _detect_router()
    monkeypatch.setattr(detect_router, "resolve_model_path", lambda s: "m.pt")
    monkeypatch.setattr(
        detect_router,
        "detect",
        lambda frame, conf, mp: [Detection(0, 0, 5, 5, "x", 0.9)],
    )
    resp = client.post("/api/detect/image", files={"file": ("a.png", _png_bytes(), "image/png")})
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["image"]
    assert body["detections"][0]["label"] == "x"


def test_detect_image_no_model_409(client, monkeypatch):
    detect_router = _detect_router()
    monkeypatch.setattr(detect_router, "resolve_model_path", lambda s: None)
    resp = client.post("/api/detect/image", files={"file": ("a.png", _png_bytes(), "image/png")})
    assert resp.status_code == 409


def test_video_upload_then_stream(client, monkeypatch):
    up = client.post("/api/detect/video", files={"file": ("v.mp4", b"data", "video/mp4")})
    assert up.status_code == 200
    vid = up.json()["video_id"]

    detect_router = _detect_router()
    monkeypatch.setattr(detect_router, "resolve_model_path", lambda s: "m.pt")

    class _Stub:
        def __init__(self, source):
            pass

        def start(self):
            return self

        def stop(self):
            pass

    monkeypatch.setattr(detect_router, "FrameGrabber", _Stub)
    monkeypatch.setattr(detect_router, "annotated_mjpeg", lambda *a, **k: iter([b"--frame\r\nX"]))
    resp = client.get(f"/api/detect/video/{vid}/stream")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("multipart/x-mixed-replace")

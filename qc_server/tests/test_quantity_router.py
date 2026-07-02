import cv2
import numpy as np

from app.services.object_detection import Detection


def _png_bytes():
    img = np.zeros((10, 10, 3), np.uint8)
    ok, buf = cv2.imencode(".png", img)
    return buf.tobytes()


def _quantity_router():
    from app.routers import quantity
    return quantity


def test_detect_image_returns_counts(client, monkeypatch):
    q = _quantity_router()
    monkeypatch.setattr(q, "resolve_named_model_path", lambda name: "m.pt")
    monkeypatch.setattr(
        q, "detect",
        lambda frame, conf, mp: [
            Detection(0, 0, 5, 5, "bolt", 0.9),
            Detection(1, 1, 6, 6, "bolt", 0.8),
            Detection(2, 2, 7, 7, "nut", 0.7),
        ],
    )
    # ensure a quantity model is set so the endpoint proceeds
    client.put("/api/settings", json={"quantity_model": "m.pt"})
    resp = client.post("/api/quantity/detect/image",
                       files={"file": ("a.png", _png_bytes(), "image/png")})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert body["per_class"] == {"bolt": 2, "nut": 1}
    assert len(body["detections"]) == 3
    assert body["width"] == 10 and body["height"] == 10


def test_detect_image_no_model_409(client, monkeypatch):
    q = _quantity_router()
    monkeypatch.setattr(q, "resolve_named_model_path", lambda name: None)
    resp = client.post("/api/quantity/detect/image",
                       files={"file": ("a.png", _png_bytes(), "image/png")})
    assert resp.status_code == 409

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
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
    captured = {}
    monkeypatch.setattr(q, "resolve_named_model_path", lambda name: "m.pt")

    def fake_detect(frame, conf, mp, **kwargs):
        captured.update(kwargs)
        return [
            Detection(0, 0, 5, 5, "bolt", 0.9),
            Detection(1, 1, 6, 6, "bolt", 0.8),
            Detection(2, 2, 7, 7, "nut", 0.7),
        ]

    monkeypatch.setattr(q, "detect", fake_detect)
    # ensure a quantity model is set so the endpoint proceeds
    client.put("/api/settings", json={
        "quantity_model": "m.pt",
        "quantity_nms_iou": 0.4,
        "quantity_agnostic_nms": False,
    })
    resp = client.post("/api/quantity/detect/image",
                       files={"file": ("a.png", _png_bytes(), "image/png")})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert body["per_class"] == {"bolt": 2, "nut": 1}
    assert len(body["detections"]) == 3
    assert body["width"] == 10 and body["height"] == 10
    assert captured == {"iou": 0.4, "agnostic_nms": False, "prompts": None}


def test_detect_image_passes_parsed_quantity_classes(client, monkeypatch):
    q = _quantity_router()
    captured = {}
    monkeypatch.setattr(q, "resolve_named_model_path", lambda name: "m.pt")

    def fake_detect(frame, conf, mp, **kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(q, "detect", fake_detect)
    client.put("/api/settings", json={
        "quantity_model": "m.pt",
        "quantity_classes": " bolt, nut, bolt,, bracket ",
    })
    resp = client.post("/api/quantity/detect/image",
                       files={"file": ("a.png", _png_bytes(), "image/png")})

    assert resp.status_code == 200
    assert captured["prompts"] == ["bolt", "nut", "bracket"]


def test_detect_image_rejects_non_prompt_model_with_classes(client, monkeypatch):
    q = _quantity_router()
    monkeypatch.setattr(q, "resolve_named_model_path", lambda name: "m.pt")
    monkeypatch.setattr(
        q,
        "detect",
        lambda *a, **k: (_ for _ in ()).throw(
            ValueError("model does not support class prompts")
        ),
    )
    client.put("/api/settings", json={"quantity_model": "m.pt", "quantity_classes": "bolt"})

    resp = client.post("/api/quantity/detect/image",
                       files={"file": ("a.png", _png_bytes(), "image/png")})

    assert resp.status_code == 409
    assert resp.json()["detail"] == (
        "selected model does not support class prompts; clear the target classes field"
    )


def test_detect_image_plain_mode_error_not_masked(client, monkeypatch):
    q = _quantity_router()
    monkeypatch.setattr(q, "resolve_named_model_path", lambda name: "m.pt")
    monkeypatch.setattr(
        q,
        "detect",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("classes required")),
    )
    client.put("/api/settings", json={"quantity_model": "m.pt", "quantity_classes": ""})

    with TestClient(app, raise_server_exceptions=False) as c:
        resp = c.post("/api/quantity/detect/image",
                      files={"file": ("a.png", _png_bytes(), "image/png")})

    assert resp.status_code == 500
    assert resp.status_code != 409


def test_detect_image_promptable_yoloe_without_classes_409(client, monkeypatch):
    q = _quantity_router()
    monkeypatch.setattr(q, "resolve_named_model_path", lambda name: "yoloe-26l-seg.pt")
    client.put("/api/settings", json={"quantity_model": "yoloe-26l-seg.pt", "quantity_classes": ""})

    resp = client.post("/api/quantity/detect/image",
                       files={"file": ("a.png", _png_bytes(), "image/png")})

    assert resp.status_code == 409
    assert resp.json()["detail"] == "enter target classes for this model"


def test_detect_image_promptfree_yoloe_empty_classes_not_guarded(client, monkeypatch):
    q = _quantity_router()
    monkeypatch.setattr(q, "resolve_named_model_path", lambda name: "yoloe-26l-seg-pf.pt")
    monkeypatch.setattr(q, "detect", lambda *a, **k: [])
    client.put("/api/settings", json={"quantity_model": "yoloe-26l-seg-pf.pt", "quantity_classes": ""})

    resp = client.post("/api/quantity/detect/image",
                       files={"file": ("a.png", _png_bytes(), "image/png")})

    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_detect_image_writes_crops_and_serves(client, monkeypatch):
    q = _quantity_router()
    monkeypatch.setattr(q, "resolve_named_model_path", lambda name: "m.pt")
    monkeypatch.setattr(
        q,
        "detect",
        lambda frame, conf, mp, **kwargs: [Detection(1, 1, 8, 8, "bolt", 0.9)],
    )
    client.put("/api/settings", json={"quantity_model": "m.pt"})
    resp = client.post(
        "/api/quantity/detect/image",
        files={"file": ("a.png", _png_bytes(), "image/png")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["crop_key"]
    assert len(body["crops"]) == 1
    assert body["crops"][0]["label"] == "bolt"
    assert body["crops"][0]["box"] == [1, 1, 8, 8]
    url = body["crops"][0]["url"]
    assert url.startswith("/api/quantity/crops/_tmp/")
    served = client.get(url)
    assert served.status_code == 200


def test_serve_missing_crop_404(client):
    assert client.get("/api/quantity/crops/_tmp/nope/x.png").status_code == 404


def test_detect_image_no_model_409(client, monkeypatch):
    q = _quantity_router()
    monkeypatch.setattr(q, "resolve_named_model_path", lambda name: None)
    resp = client.post("/api/quantity/detect/image",
                       files={"file": ("a.png", _png_bytes(), "image/png")})
    assert resp.status_code == 409


def test_detect_camera_returns_crops_and_frame(client, monkeypatch):
    q = _quantity_router()
    client.post("/api/cameras", json={"id": "cam-1", "name": "C", "type": "usb", "source": "0"})
    client.put("/api/settings", json={"quantity_model": "m.pt"})
    monkeypatch.setattr(q, "resolve_named_model_path", lambda name: "m.pt")
    monkeypatch.setattr(q, "detect", lambda *a, **k: [Detection(1, 1, 8, 8, "pcb", 0.9)])
    monkeypatch.setattr(q, "grab_one", lambda src: np.zeros((10, 10, 3), np.uint8))

    resp = client.post("/api/quantity/detect/camera/cam-1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["crops"]) == 1
    assert body["crops"][0]["box"] == [1, 1, 8, 8]
    assert body["frame_url"].endswith("/frame.jpg")

    assert client.post("/api/quantity/detect/camera/nope").status_code == 404
    monkeypatch.setattr(q, "grab_one", lambda src: None)
    assert client.post("/api/quantity/detect/camera/cam-1").status_code == 503

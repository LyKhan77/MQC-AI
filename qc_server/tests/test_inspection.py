import io

import cv2
import numpy as np

from app.services.inference.base import Detection


def _png_bytes():
    frame = np.zeros((40, 40, 3), np.uint8)
    frame[10:30, 10:30] = 200
    ok, buf = cv2.imencode(".png", frame)
    assert ok
    return buf.tobytes()


def test_detect_image_returns_key_and_defects(client):
    files = {"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")}
    resp = client.post("/api/inspection/detect", files=files, data={"crop_mode": "full"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["key"]
    assert body["verdict"] in ("clean", "defect")
    assert isinstance(body["defects"], list)
    assert client.get(body["frame_url"]).status_code == 200


def test_detect_auto_crop_mode_ok(client):
    files = {"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")}
    resp = client.post("/api/inspection/detect", files=files, data={"crop_mode": "auto"})
    assert resp.status_code == 200
    assert resp.json()["crop_mode"] == "auto"


def test_detect_auto_crop_debug_returns_original_frame_overlay(client):
    files = {"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")}
    resp = client.post(
        "/api/inspection/detect",
        files=files,
        data={"crop_mode": "auto", "debug_crop": "true"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["debug_frame_url"].endswith("/debug.jpg")
    debug = cv2.imdecode(np.frombuffer(client.get(body["debug_frame_url"]).content, np.uint8), cv2.IMREAD_COLOR)
    assert debug.shape[:2] == (40, 40)


def test_detect_rejects_bad_image(client):
    files = {"file": ("x.png", io.BytesIO(b"not an image"), "image/png")}
    resp = client.post("/api/inspection/detect", files=files, data={"crop_mode": "full"})
    assert resp.status_code == 400


def test_detect_rejects_empty_sam_model(client, tmp_path, monkeypatch):
    from app.config import settings as app_settings

    monkeypatch.setattr(app_settings, "models_dir", str(tmp_path))
    (tmp_path / "sam3.pt").write_bytes(b"")
    client.put("/api/settings", json={
        "defect_strategy": "sam3_prompt",
        "qc_model": "sam3.pt",
    })

    resp = client.post(
        "/api/inspection/detect",
        files={"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")},
        data={"crop_mode": "full"},
    )

    assert resp.status_code == 409
    assert resp.json()["detail"] == "QC model file is empty: sam3.pt"


def test_to_qc_creates_done_batch_from_captures(client):
    captures = []
    for _ in range(2):
        files = {"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")}
        resp = client.post("/api/inspection/detect", files=files, data={"crop_mode": "full"})
        captures.append({"key": resp.json()["key"], "defects": []})

    resp = client.post("/api/inspection/to-qc", json={"captures": captures})
    assert resp.status_code == 201
    batch_id = resp.json()["batch_id"]
    assert client.get(f"/api/batches/{batch_id}/status").json()["status"] == "done"
    images = client.get(f"/api/batches/{batch_id}").json()["images"]
    assert len(images) == 2
    assert all(im["status"] == "clean" and im["defects"] == [] for im in images)


class _OneDefectStrategy:
    def detect(self, *args, **kwargs):
        return [Detection("scratch", "coating", 0.9, [[1, 1], [10, 1], [10, 10]])]


def test_to_qc_persists_defects_as_done_batch(client, monkeypatch):
    from app.routers import inspection

    monkeypatch.setattr(inspection, "get_strategy", lambda _: _OneDefectStrategy())
    files = {"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")}
    detected = client.post("/api/inspection/detect", files=files, data={"crop_mode": "full"}).json()
    assert detected["defects"]

    resp = client.post(
        "/api/inspection/to-qc",
        json={"captures": [{"key": detected["key"], "defects": detected["defects"]}]},
    )

    assert resp.status_code == 201
    batch_id = resp.json()["batch_id"]
    assert client.get(f"/api/batches/{batch_id}/status").json()["status"] == "done"
    image = client.get(f"/api/batches/{batch_id}").json()["images"][0]
    assert image["status"] == "defect"
    assert len(image["defects"]) == len(detected["defects"])


def test_to_qc_rejects_empty(client):
    assert client.post("/api/inspection/to-qc", json={"captures": []}).status_code == 400


def test_to_qc_rejects_key_traversal(client):
    resp = client.post("/api/inspection/to-qc", json={"captures": [{"key": "../..", "defects": []}]})
    assert resp.status_code == 400

import io

import cv2
import numpy as np


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


def test_detect_rejects_bad_image(client):
    files = {"file": ("x.png", io.BytesIO(b"not an image"), "image/png")}
    resp = client.post("/api/inspection/detect", files=files, data={"crop_mode": "full"})
    assert resp.status_code == 400


def test_to_qc_creates_pending_batch_from_keys(client):
    keys = []
    for _ in range(2):
        files = {"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")}
        resp = client.post("/api/inspection/detect", files=files, data={"crop_mode": "full"})
        keys.append(resp.json()["key"])

    resp = client.post("/api/inspection/to-qc", json={"keys": keys})
    assert resp.status_code == 201
    batch_id = resp.json()["batch_id"]
    assert client.get(f"/api/batches/{batch_id}/status").json()["status"] == "pending"
    assert len(client.get(f"/api/batches/{batch_id}").json()["images"]) == 2


def test_to_qc_rejects_empty(client):
    assert client.post("/api/inspection/to-qc", json={"keys": []}).status_code == 400


def test_to_qc_rejects_key_traversal(client):
    resp = client.post("/api/inspection/to-qc", json={"keys": ["../.."]})
    assert resp.status_code == 400

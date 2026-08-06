import io
import json

import cv2
import numpy as np

from app.services.inference.base import Detection
from app.routers import inspection


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


def test_detect_rejects_invalid_mask_polygon(client):
    response = client.post(
        "/api/inspection/detect",
        files={"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")},
        data={"mask_polygon": json.dumps([[1, 1], [2, 2]])},
    )
    assert response.status_code == 400


def test_detect_rejects_malformed_mask_polygon(client):
    response = client.post(
        "/api/inspection/detect",
        files={"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")},
        data={"mask_polygon": "not-json"},
    )
    assert response.status_code == 400


def test_detect_mask_returns_full_image_coordinates(client, monkeypatch):
    class RoiStrategy:
        def detect(self, image_path, width, height, defect_classes, params):
            assert image_path.endswith("roi.jpg")
            assert (width, height) == (20, 20)
            return [Detection("scratch", "coating", 0.9, [[1, 1], [4, 1], [4, 4]])]

    monkeypatch.setattr(inspection, "get_strategy", lambda _: RoiStrategy())
    response = client.post(
        "/api/inspection/detect",
        files={"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")},
        data={
            "crop_mode": "auto",
            "mask_polygon": json.dumps([[10, 10], [30, 10], [30, 30], [10, 30]]),
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mask_applied"] is True
    assert body["width"] == 40 and body["height"] == 40
    assert body["defects"][0]["polygon"] == [[11, 11], [14, 11], [14, 14]]
    saved = cv2.imdecode(np.frombuffer(client.get(body["frame_url"]).content, np.uint8), cv2.IMREAD_COLOR)
    assert saved.shape[:2] == (40, 40)


def test_detect_without_mask_keeps_full_frame_inference(client, monkeypatch):
    class FullFrameStrategy:
        def detect(self, image_path, width, height, defect_classes, params):
            assert (width, height) == (40, 40)
            return [Detection("scratch", "coating", 0.9, [[1, 1], [4, 1], [4, 4]])]

    monkeypatch.setattr(inspection, "get_strategy", lambda _: FullFrameStrategy())
    body = client.post(
        "/api/inspection/detect",
        files={"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")},
        data={"crop_mode": "full"},
    ).json()
    assert body["mask_applied"] is False
    assert body["mask_polygon"] is None
    assert body["width"] == 40 and body["height"] == 40
    assert body["defects"][0]["polygon"] == [[1, 1], [4, 1], [4, 4]]


def test_detect_mask_bypasses_auto_crop(client, monkeypatch):
    class RoiStrategy:
        def detect(self, *args, **kwargs):
            return []

    monkeypatch.setattr(inspection, "get_strategy", lambda _: RoiStrategy())
    monkeypatch.setattr(inspection, "analyze_autocrop", lambda *_: (_ for _ in ()).throw(AssertionError("called")))
    response = client.post(
        "/api/inspection/detect",
        files={"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")},
        data={
            "crop_mode": "auto",
            "mask_polygon": json.dumps([[10, 10], [30, 10], [30, 30], [10, 30]]),
        },
    )
    assert response.status_code == 200
    assert response.json()["crop_box"] is None


def test_detect_mask_discards_defects_outside_polygon(client, monkeypatch):
    class RoiStrategy:
        def detect(self, *args, **kwargs):
            return [Detection("scratch", "coating", 0.9, [[0, 0], [3, 0], [0, 3]])]

    monkeypatch.setattr(inspection, "get_strategy", lambda _: RoiStrategy())
    body = client.post(
        "/api/inspection/detect",
        files={"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")},
        data={"mask_polygon": json.dumps([[20, 10], [30, 20], [20, 30], [10, 20]])},
    ).json()
    assert body["defects"] == []


def test_autocrop_preview_returns_box_and_quality(client):
    files = {"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")}
    resp = client.post("/api/inspection/autocrop-preview", files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert body["width"] == 40
    assert body["height"] == 40
    assert body["quality"]["status"] in {"ok", "review", "reject"}
    assert body["quality"]["candidate_count"] >= 1


def test_auto_crop_result_includes_quality_gate(client):
    files = {"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")}
    body = client.post("/api/inspection/detect", files=files, data={"crop_mode": "auto"}).json()
    assert body["crop_quality"]["status"] in {"ok", "review", "reject"}
    assert body["source_width"] == 40


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


def test_to_qc_persists_capture_mask_polygon(client, monkeypatch):
    monkeypatch.setattr(inspection, "get_strategy", lambda _: _OneDefectStrategy())
    polygon = [[10, 10], [30, 10], [30, 30], [10, 30]]
    detected = client.post(
        "/api/inspection/detect",
        files={"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")},
        data={"mask_polygon": json.dumps(polygon)},
    ).json()

    response = client.post(
        "/api/inspection/to-qc",
        json={"captures": [{
            "key": detected["key"],
            "defects": detected["defects"],
            "mask_polygon": detected["mask_polygon"],
        }]},
    )

    assert response.status_code == 201
    image = client.get(f"/api/batches/{response.json()['batch_id']}").json()["images"][0]
    assert image["mask_polygon"] == polygon


def test_to_qc_rejects_malformed_or_invalid_mask_before_moving_capture(client):
    valid = client.post(
        "/api/inspection/detect",
        files={"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")},
    ).json()
    invalid = client.post(
        "/api/inspection/detect",
        files={"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")},
    ).json()

    for mask_polygon in ("bad", [[1, 1], [2, 2]]):
        response = client.post(
            "/api/inspection/to-qc",
            json={"captures": [
                {"key": valid["key"], "defects": []},
                {"key": invalid["key"], "defects": [], "mask_polygon": mask_polygon},
            ]},
        )
        assert response.status_code == 400
    assert client.get(valid["frame_url"]).status_code == 200
    assert client.get(invalid["frame_url"]).status_code == 200


def test_to_qc_rejects_duplicate_capture_before_moving_it(client):
    detected = client.post(
        "/api/inspection/detect",
        files={"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")},
    ).json()

    raise_server_exceptions = client._transport.raise_server_exceptions
    client._transport.raise_server_exceptions = False
    try:
        response = client.post(
            "/api/inspection/to-qc",
            json={"captures": [
                {"key": detected["key"], "defects": []},
                {"key": detected["key"], "defects": []},
            ]},
        )
    finally:
        client._transport.raise_server_exceptions = raise_server_exceptions

    assert response.status_code == 400
    assert client.get(detected["frame_url"]).status_code == 200


def test_to_qc_rejects_empty(client):
    assert client.post("/api/inspection/to-qc", json={"captures": []}).status_code == 400


def test_to_qc_rejects_key_traversal(client):
    resp = client.post("/api/inspection/to-qc", json={"captures": [{"key": "../..", "defects": []}]})
    assert resp.status_code == 400

import json

import cv2
import numpy as np


def _png_bytes():
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    cv2.rectangle(frame, (20, 30), (140, 90), (255, 255, 255), 3)
    ok, buffer = cv2.imencode(".png", frame)
    assert ok
    return buffer.tobytes()


def _calibration():
    return json.dumps({
        "point_a": [0, 0],
        "point_b": [100, 0],
        "known_mm": 50,
    })


def _process_upload(client):
    return client.post(
        "/api/measurements/process",
        files={"file": ("bracket.png", _png_bytes(), "image/png")},
        data={"calibration": _calibration()},
    )


def test_process_upload_returns_candidates_and_serves_frame(client):
    response = _process_upload(client)

    assert response.status_code == 200
    body = response.json()
    assert body["source_type"] == "image"
    assert body["source_filename"] == "bracket.png"
    assert body["readiness"] == "ready"
    assert body["candidates"]
    assert body["frame_url"].startswith("/api/measurements/files/tmp-")
    assert client.get(body["frame_url"]).status_code == 200


def test_process_live_camera_uses_registered_camera_and_grab_one(client, monkeypatch):
    from app.routers import measurements

    client.post(
        "/api/cameras",
        json={"id": "cam-measure", "name": "QC Top", "type": "usb", "source": "0"},
    )
    monkeypatch.setattr(measurements, "grab_one", lambda source: cv2.imdecode(
        np.frombuffer(_png_bytes(), np.uint8), cv2.IMREAD_COLOR
    ))

    response = client.post(
        "/api/measurements/process",
        data={"camera_id": "cam-measure", "calibration": _calibration()},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_type"] == "live_camera"
    assert body["source_camera_id"] == "cam-measure"
    assert body["source_filename"] == "cam-measure.jpg"


def test_process_mobile_camera_file_preserves_mobile_source_type(client):
    response = client.post(
        "/api/measurements/process",
        files={"file": ("mobile.jpg", _png_bytes(), "image/jpeg")},
        data={"source_type": "mobile_camera", "calibration": _calibration()},
    )

    assert response.status_code == 200
    assert response.json()["source_type"] == "mobile_camera"


def test_process_rejects_unknown_file_source_type(client):
    response = client.post(
        "/api/measurements/process",
        files={"file": ("capture.jpg", _png_bytes(), "image/jpeg")},
        data={"source_type": "camera", "calibration": _calibration()},
    )

    assert response.status_code == 400


def test_process_rejects_missing_calibration(client):
    response = client.post(
        "/api/measurements/process",
        files={"file": ("bracket.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 422


def test_process_rejects_invalid_image(client):
    response = client.post(
        "/api/measurements/process",
        files={"file": ("broken.png", b"not-an-image", "image/png")},
        data={"calibration": _calibration()},
    )

    assert response.status_code == 400


def test_process_rejects_unknown_camera(client):
    response = client.post(
        "/api/measurements/process",
        data={"camera_id": "missing", "calibration": _calibration()},
    )

    assert response.status_code == 404


def test_process_rejects_unavailable_live_camera(client, monkeypatch):
    from app.routers import measurements

    client.post(
        "/api/cameras",
        json={"id": "cam-offline", "name": "Offline", "type": "usb", "source": "0"},
    )
    monkeypatch.setattr(measurements, "grab_one", lambda source: None)

    response = client.post(
        "/api/measurements/process",
        data={"camera_id": "cam-offline", "calibration": _calibration()},
    )

    assert response.status_code == 503


def test_save_list_detail_delete_measurement_and_audit(client):
    processed = _process_upload(client).json()
    payload = {
        "name": "BRKT-001",
        "source_key": processed["source_key"],
        "source_filename": processed["source_filename"],
        "source_type": processed["source_type"],
        "calibration": processed["calibration"],
        "items": [{
            "id": "E1",
            "type": "edge_length",
            "label": "Overall length",
            "points": [[20, 30], [140, 30]],
            "nominal": 60,
            "tolerance": 2,
            "confidence": 0.95,
        }],
    }

    saved = client.post("/api/measurements", json=payload)

    assert saved.status_code == 201
    body = saved.json()
    assert body["name"] == "BRKT-001"
    assert body["items"][0]["measured"] == 60
    assert body["items"][0]["status"] == "PASS"
    assert client.get(body["source_url"]).status_code == 200

    listed = client.get("/api/measurements").json()
    assert listed[0]["id"] == body["id"]
    assert client.get(f"/api/measurements/{body['id']}").json()["name"] == "BRKT-001"
    assert any(item["action"] == "MEASUREMENT_SAVED" for item in client.get("/api/audit").json())

    deleted = client.delete(f"/api/measurements/{body['id']}")

    assert deleted.status_code == 200
    assert client.get(f"/api/measurements/{body['id']}").status_code == 404
    assert client.get(body["source_url"]).status_code == 404
    assert any(item["action"] == "MEASUREMENT_DELETED" for item in client.get("/api/audit").json())


def test_save_rejects_missing_tolerance_with_review_not_pass(client):
    processed = _process_upload(client).json()
    payload = {
        "name": "BRKT-REVIEW",
        "source_key": processed["source_key"],
        "source_filename": processed["source_filename"],
        "source_type": processed["source_type"],
        "calibration": processed["calibration"],
        "items": [{
            "id": "E1",
            "type": "edge_length",
            "points": [[20, 30], [140, 30]],
            "nominal": None,
            "tolerance": None,
            "confidence": 0.95,
        }],
    }

    response = client.post("/api/measurements", json=payload)

    assert response.status_code == 201
    assert response.json()["summary"]["status"] == "REVIEW"

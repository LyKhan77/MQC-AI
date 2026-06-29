import numpy as np

import app.routers.cameras as cameras_router
import app.services.crop_session as cs
from app.services.object_detection import Detection


def _camera(client):
    client.post(
        "/api/cameras",
        json={"id": "cam-cr", "name": "CR", "type": "rtsp", "source": "rtsp://x",
              "count_mode": "single"},
    )


def test_finalize_empty_when_never_started(client):
    _camera(client)
    body = client.post("/api/cameras/cam-cr/crop-session/finalize").json()
    assert body == {"count": 0, "folder": None, "crop_urls": []}


def test_finalize_returns_crops_and_serves_them(client, tmp_path, monkeypatch):
    _camera(client)
    monkeypatch.setattr(cs.settings, "data_dir", str(tmp_path))
    session = cs.reset_session("cam-cr")
    session.add_captured(np.zeros((100, 100, 3), dtype=np.uint8),
                         [Detection(10, 10, 40, 40, "o", 0.9)])
    body = client.post("/api/cameras/cam-cr/crop-session/finalize").json()
    assert body["count"] == 1
    assert len(body["crop_urls"]) == 1

    served = client.get(body["crop_urls"][0])
    assert served.status_code == 200
    assert served.headers["content-type"].startswith("image/")


def test_serve_missing_crop_404(client):
    _camera(client)
    assert client.get("/api/cameras/cam-cr/crops/2020-01-01-00-00-00/obj_000.jpg").status_code == 404


def test_start_resets_and_returns_ts(client, tmp_path, monkeypatch):
    _camera(client)
    monkeypatch.setattr(cs.settings, "data_dir", str(tmp_path))
    body = client.post("/api/cameras/cam-cr/crop-session/start").json()
    assert body["session_ts"]


def test_capture_appends_crops(client, tmp_path, monkeypatch):
    _camera(client)
    monkeypatch.setattr(cs.settings, "data_dir", str(tmp_path))
    monkeypatch.setattr(cameras_router, "resolve_model_path", lambda setting: "m.pt")
    monkeypatch.setattr(cameras_router, "grab_one", lambda source: np.zeros((100, 100, 3), dtype=np.uint8))
    monkeypatch.setattr(cameras_router, "detect",
                        lambda frame, conf, model_path: [Detection(10, 10, 40, 40, "o", 0.9)])
    client.post("/api/cameras/cam-cr/crop-session/start")
    body = client.post("/api/cameras/cam-cr/capture").json()
    assert body["captured"] == 1
    assert body["total_count"] == 1
    assert len(body["crop_urls"]) == 1


def test_capture_no_model_409(client, monkeypatch):
    _camera(client)
    monkeypatch.setattr(cameras_router, "resolve_model_path", lambda setting: None)
    assert client.post("/api/cameras/cam-cr/capture").status_code == 409


def test_approve_copies_selected(client, tmp_path, monkeypatch):
    _camera(client)
    monkeypatch.setattr(cs.settings, "data_dir", str(tmp_path))
    session = cs.reset_session("cam-cr")
    session.add_captured(np.zeros((100, 100, 3), dtype=np.uint8),
                         [Detection(10, 10, 40, 40, "o", 0.9), Detection(50, 50, 90, 90, "o", 0.8)])
    files = session.finalize()["files"]
    body = client.post("/api/cameras/cam-cr/crop-session/approve", json={"files": [files[0]]}).json()
    assert body["count"] == 1
    assert body["folder"].endswith("approved")


def test_approve_empty_400(client, tmp_path, monkeypatch):
    _camera(client)
    monkeypatch.setattr(cs.settings, "data_dir", str(tmp_path))
    cs.reset_session("cam-cr")
    assert client.post("/api/cameras/cam-cr/crop-session/approve", json={"files": []}).status_code == 400

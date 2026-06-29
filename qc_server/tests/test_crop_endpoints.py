import numpy as np

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
    session.add_clean_frame(np.zeros((100, 100, 3), dtype=np.uint8),
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

import app.routers.cameras as cameras_router


def _camera(client):
    client.post(
        "/api/cameras",
        json={"id": "cam-ds", "name": "DS", "type": "rtsp", "source": "rtsp://x"},
    )


def test_detect_stream_returns_multipart(client, monkeypatch):
    _camera(client)

    class StubGrabber:
        def __init__(self, source):
            pass

        def start(self):
            return self

        def stop(self):
            pass

    monkeypatch.setattr(cameras_router, "resolve_model_path", lambda setting: "m.pt")
    monkeypatch.setattr(cameras_router, "FrameGrabber", StubGrabber)
    monkeypatch.setattr(
        cameras_router,
        "annotated_mjpeg",
        lambda grabber, count_mode, conf, model_path, on_count: iter([b"--frame\r\nX"]),
    )
    resp = client.get("/api/cameras/cam-ds/detect-stream")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("multipart/x-mixed-replace")


def test_detect_stream_no_model_409(client, monkeypatch):
    _camera(client)
    monkeypatch.setattr(cameras_router, "resolve_model_path", lambda setting: None)
    assert client.get("/api/cameras/cam-ds/detect-stream").status_code == 409


def test_count_defaults_zero(client):
    _camera(client)
    assert client.get("/api/cameras/cam-ds/count").json() == {"count": 0}

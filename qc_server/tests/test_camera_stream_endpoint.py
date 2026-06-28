import app.routers.cameras as cameras_router


def _make_camera(client):
    client.post("/api/cameras", json={
        "id": "cam-stream",
        "name": "S",
        "type": "rtsp",
        "source": "rtsp://x",
    })


def test_stream_returns_multipart(client, monkeypatch):
    _make_camera(client)
    monkeypatch.setattr(cameras_router, "mjpeg_frames", lambda source: iter([b"--frame\r\nX"]))
    resp = client.get("/api/cameras/cam-stream/stream")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("multipart/x-mixed-replace")
    assert b"--frame" in resp.content


def test_stream_unknown_camera_404(client):
    assert client.get("/api/cameras/nope/stream").status_code == 404

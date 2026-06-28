import pytest
from starlette.websockets import WebSocketDisconnect

import app.routers.cameras as cameras_router


def test_detect_ws_forwards_messages(client, monkeypatch):
    client.post("/api/cameras", json={
        "id": "cam-d",
        "name": "D",
        "type": "rtsp",
        "source": "rtsp://x",
    })
    fake = [
        {"frame": "AAA", "detections": [{"box": [0, 0, 1, 1], "label": "x",
                                         "confidence": 0.9, "track_id": 1}], "count": 1},
        {"frame": "BBB", "detections": [], "count": 1},
    ]
    monkeypatch.setattr(cameras_router.settings, "model_path", "model.pt")
    monkeypatch.setattr(
        cameras_router,
        "detection_messages",
        lambda camera, conf_threshold: iter(fake),
    )

    with client.websocket_connect("/api/cameras/cam-d/detect") as ws:
        assert ws.receive_json() == fake[0]
        assert ws.receive_json() == fake[1]


def test_detect_ws_unknown_camera_closes(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/cameras/nope/detect") as ws:
            ws.receive_json()

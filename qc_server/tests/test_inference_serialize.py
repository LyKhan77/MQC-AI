from app.services.object_detection import Detection, serialize_detections


def test_serialize_detections_shape():
    dets = [
        Detection(x1=10, y1=20, x2=110, y2=220, label="sheet", confidence=0.91, track_id=3),
        Detection(x1=0, y1=0, x2=5, y2=5, label="sheet", confidence=0.7),
    ]
    out = serialize_detections(dets)
    assert out[0] == {
        "box": [10, 20, 110, 220], "label": "sheet", "confidence": 0.91, "track_id": 3,
    }
    assert out[1]["track_id"] is None

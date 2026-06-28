from app.database import SessionLocal
from app.models import Camera
from app.services import camera_monitor


def test_poll_once_sets_status_from_probe():
    db = SessionLocal()
    try:
        db.add(Camera(id="c-on", name="on", type="rtsp", source="rtsp://up", status="offline"))
        db.add(Camera(id="c-off", name="off", type="rtsp", source="rtsp://down", status="online"))
        db.commit()
    finally:
        db.close()

    def fake_probe(source):
        return source == "rtsp://up"

    db = SessionLocal()
    try:
        camera_monitor.poll_once(db, probe_fn=fake_probe)
    finally:
        db.close()

    db = SessionLocal()
    try:
        assert db.get(Camera, "c-on").status == "online"
        assert db.get(Camera, "c-off").status == "offline"
    finally:
        db.close()

from app.database import SessionLocal
from app.models import Camera


def test_camera_round_trip():
    db = SessionLocal()
    try:
        db.add(Camera(
            id="cam-test", name="Test", type="usb", source="/dev/video0",
            location="Lab", status="online", resolution="640x480", fps=15,
            count_mode="single",
        ))
        db.commit()
        loaded = db.get(Camera, "cam-test")
        assert loaded.name == "Test"
        assert loaded.count_mode == "single"
    finally:
        db.close()

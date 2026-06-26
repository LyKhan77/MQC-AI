from sqlalchemy.orm import Session

from ..models import Camera, DefectClass, Setting

_CAMERAS = [
    dict(id="cam-01", name="RaspyCam-01", type="rpi", source="csi://0",
         location="Line A - Welding", status="online", resolution="1280x720",
         fps=30, count_mode="single"),
    dict(id="cam-02", name="RTSP-Cam-02", type="rtsp",
         source="rtsp://192.168.1.60:554/stream", location="Line B - Coating",
         status="online", resolution="1920x1080", fps=25, count_mode="tracking"),
    dict(id="cam-03", name="USB-Cam-03", type="usb", source="/dev/video0",
         location="Line C - Assembly", status="offline", resolution="640x480",
         fps=15, count_mode="single"),
]

_DEFECT_CLASSES = [
    dict(id="dc-porosity", name="porosity", category="welding", color="#fa4d56"),
    dict(id="dc-spatter", name="spatter", category="welding", color="#ff832b"),
    dict(id="dc-scratch", name="scratch", category="coating", color="#4589ff"),
    dict(id="dc-color", name="color", category="coating", color="#08bdba"),
]


def seed_if_empty(db: Session) -> None:
    if db.query(Camera).count() == 0:
        db.add_all(Camera(**c) for c in _CAMERAS)
    if db.query(DefectClass).count() == 0:
        db.add_all(DefectClass(**c) for c in _DEFECT_CLASSES)
    if db.get(Setting, 1) is None:
        db.add(Setting(id=1))
    db.commit()

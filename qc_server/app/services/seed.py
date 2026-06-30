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
    dict(id="dc-scratch", name="scratch", category="coating", color="#4589ff", enabled=True),
    dict(id="dc-dent", name="dent", category="coating", color="#6929c4", enabled=True),
    dict(id="dc-color", name="discoloration", category="coating", color="#08bdba", enabled=True),
    dict(id="dc-contamination", name="contamination", category="coating", color="#009d9a", enabled=True),
    dict(id="dc-blister", name="blister", category="coating", color="#ee5396", enabled=True),
    dict(id="dc-orange-peel", name="orange peel", category="coating", color="#ff832b", enabled=False),
    dict(id="dc-run-sag", name="run / sag", category="coating", color="#b28600", enabled=False),
    dict(id="dc-pinhole", name="pinhole", category="coating", color="#1192e8", enabled=True),
    dict(id="dc-fish-eye", name="fish-eye", category="coating", color="#fa4d56", enabled=False),
    dict(id="dc-peeling", name="peeling", category="coating", color="#198038", enabled=True),
    dict(id="dc-chip", name="chip", category="coating", color="#a56eff", enabled=True),
    dict(id="dc-bare-spot", name="bare spot", category="coating", color="#570408", enabled=False),
    dict(id="dc-overspray", name="overspray", category="coating", color="#9f1853", enabled=False),
    dict(id="dc-porosity", name="porosity", category="welding", color="#fa4d56", enabled=True),
    dict(id="dc-spatter", name="spatter", category="welding", color="#ff832b", enabled=True),
    dict(id="dc-crack", name="crack", category="welding", color="#da1e28", enabled=True),
    dict(id="dc-undercut", name="undercut", category="welding", color="#d12771", enabled=True),
    dict(id="dc-incomplete-penetration", name="incomplete penetration", category="welding", color="#8a3ffc", enabled=True),
    dict(id="dc-lack-of-fusion", name="lack of fusion", category="welding", color="#d2a106", enabled=True),
    dict(id="dc-overlap", name="overlap", category="welding", color="#007d79", enabled=False),
    dict(id="dc-burn-through", name="burn-through", category="welding", color="#9f1853", enabled=True),
    dict(id="dc-slag-inclusion", name="slag inclusion", category="welding", color="#ba4e00", enabled=True),
    dict(id="dc-excessive-reinforcement", name="excessive reinforcement", category="welding", color="#491d8b", enabled=False),
    dict(id="dc-arc-strike", name="arc strike", category="welding", color="#005d5d", enabled=False),
    dict(id="dc-distortion", name="distortion", category="welding", color="#6f6f6f", enabled=False),
]


def seed_if_empty(db: Session) -> None:
    if db.query(Camera).count() == 0:
        db.add_all(Camera(**c) for c in _CAMERAS)
    for c in _DEFECT_CLASSES:
        if db.get(DefectClass, c["id"]) is None:
            db.add(DefectClass(**c))
    if db.get(Setting, 1) is None:
        db.add(Setting(id=1))
    db.commit()

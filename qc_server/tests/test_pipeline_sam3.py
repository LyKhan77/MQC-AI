import os

from PIL import Image as PILImage

from app.database import SessionLocal
from app.models import Batch, DefectClass, Setting
from app.services import pipeline
from app.services.inference.base import register
from app.util import now_iso


def _make_images(folder):
    os.makedirs(folder, exist_ok=True)
    PILImage.new("RGB", (640, 480), (30, 30, 30)).save(os.path.join(folder, "weld_1.jpg"))


def test_run_batch_passes_resolved_qc_model_path(tmp_path):
    folder = str(tmp_path / "crops")
    _make_images(folder)

    captured = {}

    class _CaptureStrategy:
        name = "capture"

        def detect(self, image_path, width, height, defect_classes, params):
            captured.update(params)
            return []

    register(_CaptureStrategy())

    db = SessionLocal()
    try:
        db.add(Setting(id=1, defect_strategy="capture", qc_model="sam3.pt",
                       confidence_threshold=0.5))
        db.add(DefectClass(id="dc-1", name="porosity", category="welding"))
        db.add(Batch(id="batch-sam3", name="Shift", source_path=folder,
                     created_at=now_iso(), status="processing"))
        db.commit()
    finally:
        db.close()

    pipeline.run_batch("batch-sam3", SessionLocal)

    assert captured["confidence_threshold"] == 0.5
    assert captured["qc_model_path"].endswith("sam3.pt")
    assert "models" in captured["qc_model_path"].replace("\\", "/")

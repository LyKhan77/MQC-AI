import os

from PIL import Image as PILImage

from app.database import SessionLocal
from app.models import Batch, DefectClass, Image, Setting
from app.services import pipeline
from app.services.inference.base import Detection, register
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
        pipeline.prepare_images(db, db.get(Batch, "batch-sam3"))
    finally:
        db.close()

    pipeline.run_batch("batch-sam3", SessionLocal)

    assert captured["confidence_threshold"] == 0.5
    assert captured["qc_model_path"].endswith("sam3.pt")
    assert "models" in captured["qc_model_path"].replace("\\", "/")


def test_run_batch_reuses_mask_roi_and_remaps_detections(tmp_path):
    folder = str(tmp_path / "crops")
    _make_images(folder)
    captured = {}

    class _MaskedStrategy:
        name = "masked-capture"

        def detect(self, image_path, width, height, defect_classes, params):
            captured.setdefault("calls", []).append((image_path, width, height))
            return [Detection("porosity", "welding", 0.9, [[1, 1], [4, 1], [4, 4]])]

    register(_MaskedStrategy())
    db = SessionLocal()
    try:
        db.add(Setting(id=1, defect_strategy="masked-capture"))
        db.add(DefectClass(id="dc-1", name="porosity", category="welding"))
        db.add(Batch(id="batch-masked", name="Masked", source_path=folder,
                     created_at=now_iso(), status="processing"))
        db.commit()
        batch = db.get(Batch, "batch-masked")
        pipeline.prepare_images(db, batch)
        image = db.query(Image).filter(Image.batch_id == batch.id).first()
        image.mask_polygon = [[10, 10], [30, 10], [30, 30], [10, 30]]
        db.commit()
    finally:
        db.close()

    pipeline.run_batch("batch-masked", SessionLocal)

    db = SessionLocal()
    try:
        image = db.query(Image).filter(Image.batch_id == "batch-masked").first()
        assert [(width, height) for _, width, height in captured["calls"]] == [(20, 20)]
        assert captured["calls"][0][0] != os.path.join(folder, image.filename)
        assert image.defects[0].polygon == [[11, 11], [14, 11], [14, 14]]
    finally:
        db.close()

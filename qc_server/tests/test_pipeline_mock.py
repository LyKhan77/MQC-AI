import os

from PIL import Image as PILImage

from app.database import SessionLocal
from app.models import Batch, DefectClass, Image, Setting
from app.services import pipeline
from app.util import now_iso


def _make_images(folder):
    os.makedirs(folder, exist_ok=True)
    for name in ["weld_0001.jpg", "weld_0002.jpg", "clean_0003.jpg"]:
        PILImage.new("RGB", (1280, 960), (40, 40, 40)).save(os.path.join(folder, name))


def test_run_batch_creates_images_and_defects(tmp_path):
    folder = str(tmp_path / "crops")
    _make_images(folder)

    db = SessionLocal()
    try:
        db.add(Setting(id=1, defect_strategy="mock"))
        db.add(DefectClass(id="dc-1", name="porosity", category="welding"))
        db.add(Batch(id="batch-1", name="Shift 1", source_path=folder,
                     created_at=now_iso(), status="processing"))
        db.commit()
    finally:
        db.close()

    pipeline.run_batch("batch-1", SessionLocal)

    db = SessionLocal()
    try:
        batch = db.get(Batch, "batch-1")
        assert batch.status == "done"
        assert batch.image_count == 3
        images = db.query(Image).filter(Image.batch_id == "batch-1").all()
        assert len(images) == 3
        clean = next(i for i in images if i.filename == "clean_0003.jpg")
        assert clean.status == "clean"
        assert clean.defects == []
    finally:
        db.close()


def test_run_batch_writes_result_json(tmp_path):
    folder = str(tmp_path / "crops2")
    _make_images(folder)
    db = SessionLocal()
    try:
        db.add(Setting(id=1, defect_strategy="mock"))
        db.add(DefectClass(id="dc-1", name="porosity", category="welding"))
        db.add(Batch(id="batch-2", name="Shift 2", source_path=folder,
                     created_at=now_iso(), status="processing"))
        db.commit()
    finally:
        db.close()

    pipeline.run_batch("batch-2", SessionLocal)

    from app.config import settings
    result_path = os.path.join(settings.data_dir, "batches", "batch-2", "result.json")
    assert os.path.exists(result_path)

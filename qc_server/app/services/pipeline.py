from .. import storage
from ..models import Batch, DefectClass, Defect, Image, Setting
from ..util import gen_id
from . import job_queue
from .inference.base import DefectClassSpec, get_strategy
from .inference import mock  # noqa: F401  (registers "mock")


def run_batch(batch_id: str, session_factory) -> None:
    db = session_factory()
    try:
        batch = db.get(Batch, batch_id)
        if batch is None:
            return

        files = storage.list_images(batch.source_path)
        job_queue.set_total(batch_id, len(files))

        setting = db.get(Setting, 1)
        strategy_name = setting.defect_strategy if setting else "mock"
        threshold = setting.confidence_threshold if setting else 0.5
        strategy = get_strategy(strategy_name)
        specs = [
            DefectClassSpec(c.name, c.category, c.enabled)
            for c in db.query(DefectClass).all()
        ]
        params = {"confidence_threshold": threshold}

        total_defects = 0
        for filename in files:
            path = storage.image_path(batch, filename)
            width, height = storage.image_size(path)
            detections = strategy.detect(path, width, height, specs, params)

            image_id = gen_id("img")
            image = Image(
                id=image_id,
                batch_id=batch_id,
                filename=filename,
                url=f"/api/images/{image_id}/file",
                width=width,
                height=height,
                status="defect" if detections else "clean",
                reviewed=False,
            )
            db.add(image)
            db.flush()
            for det in detections:
                db.add(Defect(
                    id=gen_id("d"),
                    image_id=image_id,
                    type=det.type,
                    category=det.category,
                    confidence=det.confidence,
                    polygon=det.polygon,
                ))
            total_defects += len(detections)
            db.commit()
            job_queue.increment(batch_id)

        batch.image_count = len(files)
        batch.defect_count = total_defects
        batch.status = "done"
        db.commit()
        storage.write_result_json(db, batch)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        failed = db.get(Batch, batch_id)
        if failed is not None:
            failed.status = "failed"
            failed.error = str(exc)
            db.commit()
        raise
    finally:
        db.close()

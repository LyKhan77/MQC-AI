import os
import tempfile

import cv2
import numpy as np

from ..config import settings as app_settings
from .. import storage
from ..models import Batch, DefectClass, Defect, Image, Setting
from ..util import gen_id
from . import job_queue
from .inference.base import DefectClassSpec, get_strategy
from .inference import mock  # noqa: F401  (registers "mock")
from .inference import sam3  # noqa: F401  (registers "sam3_prompt")
from .polygon_mask import polygon_has_overlap, prepare_polygon_roi, remap_polygon, validate_polygon


def prepare_images(db, batch, commit=True) -> int:
    """Create raw (un-segmented) image rows for a batch's source folder."""
    files = storage.list_images(batch.source_path)
    for filename in files:
        path = storage.image_path(batch, filename)
        width, height = storage.image_size(path)
        image_id = gen_id("img")
        db.add(Image(
            id=image_id,
            batch_id=batch.id,
            filename=filename,
            url=f"/api/images/{image_id}/file",
            width=width,
            height=height,
            status="pending",
            reviewed=False,
        ))
    batch.image_count = len(files)
    if commit:
        db.commit()
    else:
        db.flush()
    return len(files)


def run_batch(batch_id: str, session_factory, confidence_override=None) -> None:
    db = session_factory()
    try:
        batch = db.get(Batch, batch_id)
        if batch is None:
            return
        batch.reviewer = None
        batch.error = None

        setting = db.get(Setting, 1)
        strategy_name = setting.defect_strategy if setting else "mock"
        threshold = setting.qc_confidence_threshold if setting else 0.5
        if confidence_override is not None:
            threshold = confidence_override
        strategy = get_strategy(strategy_name)
        specs = [
            DefectClassSpec(c.name, c.category, c.enabled)
            for c in db.query(DefectClass).all()
        ]
        qc_model = setting.qc_model if setting else ""
        qc_model_path = (
            os.path.join(app_settings.models_dir, qc_model) if qc_model else ""
        )
        params = {
            "confidence_threshold": threshold,
            "qc_model_path": qc_model_path,
            "qc_device": setting.qc_device if setting else "auto",
        }

        images = db.query(Image).filter(Image.batch_id == batch_id).all()
        job_queue.set_total(batch_id, len(images))

        total_defects = 0
        for image in images:
            path = storage.image_path(batch, image.filename)
            if image.mask_polygon:
                frame = cv2.imread(path)
                if frame is None:
                    raise ValueError(f"invalid source image: {image.filename}")
                polygon = validate_polygon(image.mask_polygon, image.width, image.height)
                roi, offset = prepare_polygon_roi(frame, polygon)
                roi_mask = np.zeros(roi.shape[:2], dtype=np.uint8)
                cv2.fillPoly(roi_mask, [np.asarray([[x - offset[0], y - offset[1]] for x, y in polygon], dtype=np.int32)], 255)
                fd, roi_path = tempfile.mkstemp(suffix=".jpg")
                os.close(fd)
                try:
                    if not cv2.imwrite(roi_path, roi):
                        raise OSError("could not write mask ROI")
                    detections = strategy.detect(roi_path, roi.shape[1], roi.shape[0], specs, params)
                finally:
                    if os.path.exists(roi_path):
                        os.unlink(roi_path)
                detections = [
                    det for det in detections
                    if polygon_has_overlap(det.polygon, roi_mask)
                ]
                for det in detections:
                    det.polygon = remap_polygon(det.polygon, *offset)
            else:
                detections = strategy.detect(path, image.width, image.height, specs, params)
            image.defects.clear()
            image.reviewed = False
            for det in detections:
                db.add(Defect(
                    id=gen_id("d"),
                    image_id=image.id,
                    type=det.type,
                    category=det.category,
                    confidence=det.confidence,
                    polygon=det.polygon,
                ))
            image.status = "defect" if detections else "clean"
            total_defects += len(detections)
            db.commit()
            job_queue.increment(batch_id)

        batch.image_count = len(images)
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

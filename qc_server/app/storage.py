import json
import os

from PIL import Image as PILImage

from .config import settings

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")


def list_images(folder: str) -> list[str]:
    if not os.path.isdir(folder):
        return []
    return sorted(
        f for f in os.listdir(folder)
        if f.lower().endswith(IMAGE_EXTENSIONS)
    )


def image_size(path: str) -> tuple[int, int]:
    with PILImage.open(path) as im:
        return im.width, im.height


def image_path(batch, filename: str) -> str:
    return os.path.join(batch.source_path, filename)


def write_result_json(db, batch) -> str:
    from .models import Image

    images = db.query(Image).filter(Image.batch_id == batch.id).all()
    payload = {
        "batch_name": batch.name,
        "source_path": batch.source_path,
        "images": [
            {
                "id": im.id,
                "filename": im.filename,
                "url": im.url,
                "width": im.width,
                "height": im.height,
                "status": im.status,
                "defects": [
                    {
                        "id": d.id,
                        "type": d.type,
                        "category": d.category,
                        "confidence": d.confidence,
                        "polygon": d.polygon,
                    }
                    for d in im.defects
                ],
            }
            for im in images
        ],
    }
    out_dir = os.path.join(settings.data_dir, "batches", batch.id)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "result.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return out_path

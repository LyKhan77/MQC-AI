import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Batch, Image
from ..storage import image_path

router = APIRouter(prefix="/api/images", tags=["images"])


@router.get("/{image_id}/file")
def serve_image(image_id: str, db: Session = Depends(get_db)):
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(404, "image not found")
    batch = db.get(Batch, image.batch_id)
    path = image_path(batch, image.filename)
    if not os.path.exists(path):
        raise HTTPException(404, "image file not found")
    return FileResponse(path)

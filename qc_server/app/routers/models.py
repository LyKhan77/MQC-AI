import os

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings as app_settings
from ..database import get_db
from .settings import get_or_create_setting

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
def list_models(db: Session = Depends(get_db)):
    folder = app_settings.models_dir
    models = []
    if os.path.isdir(folder):
        models = sorted(f for f in os.listdir(folder) if f.lower().endswith(".pt"))
    return {"models": models, "active": get_or_create_setting(db).active_model}

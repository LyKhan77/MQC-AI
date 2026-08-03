from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Setting
from ..schemas import SettingOut, SettingUpdate
from ..services import gpu as gpu_service

router = APIRouter(prefix="/api/settings", tags=["settings"])


def get_or_create_setting(db: Session) -> Setting:
    setting = db.get(Setting, 1)
    if not setting:
        setting = Setting(id=1)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


@router.get("", response_model=SettingOut)
def read_settings(db: Session = Depends(get_db)):
    return get_or_create_setting(db)


@router.put("", response_model=SettingOut)
def update_settings(payload: SettingUpdate, db: Session = Depends(get_db)):
    setting = get_or_create_setting(db)
    values = payload.model_dump(exclude_none=True)
    inventory = None
    if any(key in values for key in ("object_detection_device", "qc_device", "quantity_device")):
        inventory = gpu_service.get_gpu_inventory()
    for key in ("object_detection_device", "qc_device", "quantity_device"):
        if key in values:
            try:
                values[key] = gpu_service.validate_device(values[key], inventory)
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc
    for key, value in values.items():
        setattr(setting, key, value)
    db.commit()
    db.refresh(setting)
    return setting

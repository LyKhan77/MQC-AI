from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Setting
from ..schemas import SettingOut, SettingUpdate

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
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(setting, key, value)
    db.commit()
    db.refresh(setting)
    return setting

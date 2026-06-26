from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog
from ..schemas import AuditLogIn, AuditLogOut
from ..util import gen_id, now_iso

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogOut])
def list_audit(db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()


@router.post("", response_model=AuditLogOut, status_code=201)
def create_audit(payload: AuditLogIn, db: Session = Depends(get_db)):
    entry = AuditLog(
        id=gen_id("log"),
        timestamp=now_iso(),
        user=payload.user,
        action=payload.action,
        detail=payload.detail,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

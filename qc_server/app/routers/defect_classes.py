import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import DefectClass
from ..schemas import DefectClassCreate, DefectClassOut

router = APIRouter(prefix="/api/defect-classes", tags=["defect-classes"])


@router.get("", response_model=list[DefectClassOut])
def list_classes(db: Session = Depends(get_db)):
    return db.query(DefectClass).all()


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return f"dc-{slug}" if slug else "dc-class"


@router.post("", response_model=DefectClassOut, status_code=201)
def create_class(payload: DefectClassCreate, db: Session = Depends(get_db)):
    cid = payload.id or _slugify(payload.name)
    if payload.id and db.get(DefectClass, cid):
        raise HTTPException(409, "defect class id already exists")
    base = cid
    i = 2
    while db.get(DefectClass, cid):
        cid = f"{base}-{i}"
        i += 1
    dc = DefectClass(id=cid, name=payload.name, category=payload.category,
                     color=payload.color, enabled=payload.enabled)
    db.add(dc)
    db.commit()
    db.refresh(dc)
    return dc


@router.patch("/{class_id}", response_model=DefectClassOut)
def patch_class(class_id: str, payload: dict, db: Session = Depends(get_db)):
    dc = db.get(DefectClass, class_id)
    if not dc:
        raise HTTPException(404, "defect class not found")
    for key, value in payload.items():
        if hasattr(dc, key) and key != "id":
            setattr(dc, key, value)
    db.commit()
    db.refresh(dc)
    return dc


@router.delete("/{class_id}")
def delete_class(class_id: str, db: Session = Depends(get_db)):
    dc = db.get(DefectClass, class_id)
    if not dc:
        raise HTTPException(404, "defect class not found")
    db.delete(dc)
    db.commit()
    return {"deleted": class_id}

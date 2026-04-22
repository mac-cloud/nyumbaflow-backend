from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Property, Unit, User
from ..schemas import PropertyCreate, PropertyOut, PropertyUpdate
from ..security import require_staff, require_roles

router = APIRouter(prefix="/properties", tags=["properties"])


def _serialize(p: Property, expand: bool, db: Session):
    out = PropertyOut.model_validate(p).model_dump(mode="json")
    if expand:
        units = db.query(Unit).filter(Unit.property_id == p.id).all()
        out["units"] = [{"id": str(u.id), "status": u.status} for u in units]
    return out


@router.get("/")
def list_properties(
    expand: bool = Query(False),
    _: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    rows = db.query(Property).order_by(Property.created_at.desc()).all()
    return [_serialize(p, expand, db) for p in rows]


@router.get("/{property_id}", response_model=PropertyOut)
def get_property(property_id: UUID, _: User = Depends(require_staff), db: Session = Depends(get_db)):
    p = db.query(Property).filter(Property.id == property_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Property not found")
    return p


@router.post("/", response_model=PropertyOut, status_code=201)
def create_property(
    payload: PropertyCreate,
    user: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    p = Property(**payload.model_dump(), created_by=user.id)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.patch("/{property_id}", response_model=PropertyOut)
def update_property(
    property_id: UUID,
    payload: PropertyUpdate,
    _: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    p = db.query(Property).filter(Property.id == property_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Property not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    p.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{property_id}", status_code=204)
def delete_property(
    property_id: UUID,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    p = db.query(Property).filter(Property.id == property_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Property not found")
    db.delete(p)
    db.commit()

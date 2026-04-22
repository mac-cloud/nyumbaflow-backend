from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Unit, User
from ..schemas import UnitCreate, UnitOut, UnitUpdate
from ..security import require_staff, require_roles

router = APIRouter(prefix="/units", tags=["units"])


@router.get("/", response_model=list[UnitOut])
def list_units(
    property_id: Optional[UUID] = None,
    status: Optional[str] = None,
    _: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    q = db.query(Unit)
    if property_id:
        q = q.filter(Unit.property_id == property_id)
    if status:
        q = q.filter(Unit.status == status)
    return q.order_by(Unit.name).all()


@router.post("/", response_model=UnitOut, status_code=201)
def create_unit(
    payload: UnitCreate,
    _: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    u = Unit(**payload.model_dump())
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.patch("/{unit_id}", response_model=UnitOut)
def update_unit(
    unit_id: UUID,
    payload: UnitUpdate,
    _: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    u = db.query(Unit).filter(Unit.id == unit_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Unit not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(u, k, v)
    u.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(u)
    return u


@router.delete("/{unit_id}", status_code=204)
def delete_unit(
    unit_id: UUID,
    _: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    u = db.query(Unit).filter(Unit.id == unit_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Unit not found")
    db.delete(u)
    db.commit()

from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Lease, Unit, Tenant, Property, User
from ..schemas import LeaseCreate, LeaseOut
from ..security import require_staff, require_roles

router = APIRouter(prefix="/leases", tags=["leases"])


def _serialize(lease: Lease, expand: bool, db: Session):
    out = LeaseOut.model_validate(lease).model_dump(mode="json")
    if expand:
        tenant = db.query(Tenant).filter(Tenant.id == lease.tenant_id).first()
        unit = db.query(Unit).filter(Unit.id == lease.unit_id).first()
        prop = db.query(Property).filter(Property.id == unit.property_id).first() if unit else None
        out["tenants"] = {"full_name": tenant.full_name} if tenant else None
        out["units"] = {
            "name": unit.name if unit else None,
            "properties": {"name": prop.name} if prop else None,
        } if unit else None
    return out


@router.get("/")
def list_leases(
    status: Optional[str] = None,
    expand: bool = Query(False),
    _: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    q = db.query(Lease)
    if status:
        q = q.filter(Lease.status == status)
    leases = q.order_by(Lease.created_at.desc()).all()
    return [_serialize(l, expand, db) for l in leases]


@router.post("/", response_model=LeaseOut, status_code=201)
def create_lease(
    payload: LeaseCreate,
    _: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    lease = Lease(**payload.model_dump())
    db.add(lease)

    unit = db.query(Unit).filter(Unit.id == payload.unit_id).first()
    if unit and lease.status == "active":
        unit.status = "occupied"
        unit.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(lease)
    return lease


@router.post("/{lease_id}/end", response_model=LeaseOut)
def end_lease(
    lease_id: UUID,
    _: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")
    lease.status = "ended"
    lease.end_date = datetime.utcnow().date()
    lease.updated_at = datetime.utcnow()

    unit = db.query(Unit).filter(Unit.id == lease.unit_id).first()
    if unit:
        unit.status = "vacant"
        unit.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(lease)
    return lease

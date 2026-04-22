from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Tenant, Lease, Unit, Property, User
from ..schemas import TenantCreate, TenantOut, TenantUpdate
from ..security import require_staff, require_roles

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _serialize(t: Tenant, expand: bool, db: Session):
    out = TenantOut.model_validate(t).model_dump(mode="json")
    if expand:
        leases = db.query(Lease).filter(Lease.tenant_id == t.id).all()
        out["leases"] = []
        for l in leases:
            unit = db.query(Unit).filter(Unit.id == l.unit_id).first()
            prop = db.query(Property).filter(Property.id == unit.property_id).first() if unit else None
            out["leases"].append({
                "id": str(l.id),
                "status": l.status,
                "units": {
                    "name": unit.name if unit else None,
                    "properties": {"name": prop.name} if prop else None,
                } if unit else None,
            })
    return out


@router.get("/")
def list_tenants(
    expand: bool = Query(False),
    _: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    rows = db.query(Tenant).order_by(Tenant.full_name).all()
    return [_serialize(t, expand, db) for t in rows]


@router.get("/{tenant_id}", response_model=TenantOut)
def get_tenant(tenant_id: UUID, _: User = Depends(require_staff), db: Session = Depends(get_db)):
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return t


@router.post("/", response_model=TenantOut, status_code=201)
def create_tenant(
    payload: TenantCreate,
    _: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    t = Tenant(**payload.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.patch("/{tenant_id}", response_model=TenantOut)
def update_tenant(
    tenant_id: UUID,
    payload: TenantUpdate,
    _: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{tenant_id}", status_code=204)
def delete_tenant(
    tenant_id: UUID,
    _: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    db.delete(t)
    db.commit()

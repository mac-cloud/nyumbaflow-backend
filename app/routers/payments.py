from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Payment, Lease, Tenant, User
from ..schemas import PaymentCreate, PaymentOut
from ..security import require_staff, require_roles

router = APIRouter(prefix="/payments", tags=["payments"])


def _serialize(p: Payment, expand: bool, db: Session):
    out = PaymentOut.model_validate(p).model_dump(mode="json")
    if expand:
        lease = db.query(Lease).filter(Lease.id == p.lease_id).first()
        tenant = db.query(Tenant).filter(Tenant.id == lease.tenant_id).first() if lease else None
        out["leases"] = {
            "tenant_id": str(lease.tenant_id) if lease else None,
            "tenants": {"full_name": tenant.full_name} if tenant else None,
        } if lease else None
    return out


@router.get("/")
def list_payments(
    lease_id: Optional[UUID] = None,
    expand: bool = Query(False),
    _: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    q = db.query(Payment)
    if lease_id:
        q = q.filter(Payment.lease_id == lease_id)
    rows = q.order_by(Payment.paid_on.desc()).all()
    return [_serialize(p, expand, db) for p in rows]


@router.post("/", response_model=PaymentOut, status_code=201)
def create_payment(
    payload: PaymentCreate,
    user: User = Depends(require_roles("admin", "manager", "accountant")),
    db: Session = Depends(get_db),
):
    p = Payment(**payload.model_dump(), recorded_by=user.id)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/summary/total")
def total_collected(_: User = Depends(require_staff), db: Session = Depends(get_db)):
    total = db.query(func.coalesce(func.sum(Payment.amount), 0)).scalar()
    return {"total_collected": float(total or 0)}

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class _Base(BaseModel):
    """Base that ignores unexpected client-supplied fields (e.g. created_by)."""
    model_config = ConfigDict(extra="ignore")


# ---------- Auth ----------
class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    full_name: str = Field(min_length=2, max_length=100)
    business_name: Optional[str] = None
    phone: Optional[str] = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileOut(BaseModel):
    id: UUID
    full_name: Optional[str] = None
    phone: Optional[str] = None
    business_name: Optional[str] = None
    avatar_url: Optional[str] = None
    class Config: from_attributes = True


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    business_name: Optional[str] = None
    avatar_url: Optional[str] = None


class MeOut(BaseModel):
    id: UUID
    email: EmailStr
    roles: List[str]
    profile: Optional[ProfileOut] = None


class TeamMemberOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    roles: List[str]


class RoleAssign(BaseModel):
    role: str  # admin | manager | caretaker | accountant | tenant


# ---------- Property ----------
class PropertyBase(_Base):
    name: str
    address: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class PropertyCreate(PropertyBase): pass
class PropertyUpdate(PropertyBase): pass


class PropertyOut(PropertyBase):
    id: UUID
    created_at: datetime
    class Config: from_attributes = True


# ---------- Unit ----------
class UnitBase(_Base):
    name: str
    unit_type: str = "bedsitter"
    rent_amount: Decimal = Decimal(0)
    deposit_amount: Decimal = Decimal(0)
    status: str = "vacant"
    notes: Optional[str] = None


class UnitCreate(UnitBase):
    property_id: UUID


class UnitUpdate(UnitBase): pass


class UnitOut(UnitBase):
    id: UUID
    property_id: UUID
    class Config: from_attributes = True


# ---------- Tenant ----------
class TenantBase(_Base):
    full_name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    national_id: Optional[str] = None
    next_of_kin_name: Optional[str] = None
    next_of_kin_phone: Optional[str] = None
    notes: Optional[str] = None


class TenantCreate(TenantBase): pass
class TenantUpdate(TenantBase): pass


class TenantOut(TenantBase):
    id: UUID
    class Config: from_attributes = True


# ---------- Lease ----------
class LeaseBase(_Base):
    tenant_id: UUID
    unit_id: UUID
    start_date: date
    end_date: Optional[date] = None
    rent_amount: Decimal
    deposit_amount: Decimal = Decimal(0)
    deposit_paid: Decimal = Decimal(0)
    status: str = "active"
    notes: Optional[str] = None


class LeaseCreate(LeaseBase): pass


class LeaseOut(LeaseBase):
    id: UUID
    class Config: from_attributes = True


# ---------- Payment ----------
class PaymentBase(_Base):
    lease_id: UUID
    amount: Decimal = Field(gt=0)
    paid_on: date
    method: str = "cash"
    reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase): pass


class PaymentOut(PaymentBase):
    id: UUID
    class Config: from_attributes = True

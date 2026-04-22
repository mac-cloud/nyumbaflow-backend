"""SQLAlchemy models for NyumbaFlow (Postgres, no Supabase)."""
from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import (
    Column, String, Text, Numeric, Date, DateTime, ForeignKey, Boolean,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base


# ---------- Auth ----------
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(Text, unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"
    id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    full_name = Column(Text)
    phone = Column(Text)
    business_name = Column(Text)
    avatar_url = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="profile")


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role", name="user_roles_user_role_uniq"),)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Text, nullable=False)  # admin | manager | caretaker | accountant | tenant
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="roles")


# ---------- Domain ----------
class Property(Base):
    __tablename__ = "properties"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(Text, nullable=False)
    address = Column(Text)
    description = Column(Text)
    image_url = Column(Text)
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    units = relationship("Unit", back_populates="property", cascade="all, delete-orphan")


class Unit(Base):
    __tablename__ = "units"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    unit_type = Column(Text, nullable=False, default="bedsitter")
    rent_amount = Column(Numeric, nullable=False, default=0)
    deposit_amount = Column(Numeric, nullable=False, default=0)
    status = Column(Text, nullable=False, default="vacant")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    property = relationship("Property", back_populates="units")


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    full_name = Column(Text, nullable=False)
    phone = Column(Text)
    email = Column(Text)
    national_id = Column(Text)
    next_of_kin_name = Column(Text)
    next_of_kin_phone = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Lease(Base):
    __tablename__ = "leases"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    rent_amount = Column(Numeric, nullable=False)
    deposit_amount = Column(Numeric, nullable=False, default=0)
    deposit_paid = Column(Numeric, nullable=False, default=0)
    status = Column(Text, nullable=False, default="active")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Payment(Base):
    __tablename__ = "payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    lease_id = Column(UUID(as_uuid=True), ForeignKey("leases.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric, nullable=False)
    paid_on = Column(Date, nullable=False, default=date.today)
    method = Column(Text, nullable=False, default="cash")
    reference = Column(Text)
    notes = Column(Text)
    recorded_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

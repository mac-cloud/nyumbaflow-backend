from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Profile, UserRole
from ..schemas import ProfileOut, ProfileUpdate, TeamMemberOut, RoleAssign
from ..security import get_current_user, require_roles, get_user_roles

router = APIRouter(prefix="/users", tags=["users"])

VALID_ROLES = {"admin", "manager", "caretaker", "accountant", "tenant"}


@router.get("/me/profile", response_model=ProfileOut)
def get_my_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/me/profile", response_model=ProfileOut)
def update_my_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(Profile).filter(Profile.id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(profile, k, v)
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/team", response_model=list[TeamMemberOut])
def list_team(_: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    users = db.query(User).all()
    out: list[TeamMemberOut] = []
    for u in users:
        profile = db.query(Profile).filter(Profile.id == u.id).first()
        out.append(TeamMemberOut(
            id=u.id, email=u.email,
            full_name=profile.full_name if profile else None,
            roles=get_user_roles(db, u.id),
        ))
    return out


@router.post("/{user_id}/roles", status_code=204)
def assign_role(
    user_id: UUID,
    payload: RoleAssign,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    if payload.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    exists = db.query(UserRole).filter(
        UserRole.user_id == user_id, UserRole.role == payload.role,
    ).first()
    if exists:
        return
    db.add(UserRole(user_id=user_id, role=payload.role))
    db.commit()


@router.delete("/{user_id}/roles/{role}", status_code=204)
def remove_role(
    user_id: UUID,
    role: str,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    db.query(UserRole).filter(
        UserRole.user_id == user_id, UserRole.role == role,
    ).delete()
    db.commit()

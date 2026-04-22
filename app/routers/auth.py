from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Profile, UserRole
from ..schemas import SignupIn, LoginIn, TokenOut, MeOut, ProfileOut
from ..security import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_user_roles,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenOut)
def signup(payload: SignupIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()

    db.add(Profile(
        id=user.id,
        full_name=payload.full_name,
        phone=payload.phone,
        business_name=payload.business_name,
    ))

    # First user is auto-admin
    is_first = db.query(User).count() == 1
    if is_first:
        db.add(UserRole(user_id=user.id, role="admin"))

    db.commit()
    return TokenOut(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    return TokenOut(access_token=create_access_token(user.id))


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == user.id).first()
    return MeOut(
        id=user.id,
        email=user.email,
        roles=get_user_roles(db, user.id),
        profile=ProfileOut.model_validate(profile) if profile else None,
    )

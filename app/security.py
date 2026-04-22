"""Password hashing + JWT helpers."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        uid = payload.get("sub")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == uid, User.is_active == True).first()  # noqa: E712
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_user_roles(db: Session, user_id: UUID) -> list[str]:
    return [r.role for r in db.query(UserRole).filter(UserRole.user_id == user_id).all()]


def require_roles(*allowed: str):
    """Dependency that ensures the user has at least one of the allowed roles."""
    def checker(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        roles = get_user_roles(db, user.id)
        if not any(r in allowed for r in roles):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker


def require_staff(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    roles = get_user_roles(db, user.id)
    if not any(r in {"admin", "manager", "caretaker", "accountant"} for r in roles):
        raise HTTPException(status_code=403, detail="Staff only")
    return user

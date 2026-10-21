from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..db import get_db
from .. import models
from ..schemas import UserCreate, UserOut, TokenOut, LoginRequest, RefreshRequest
from ..security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["auth"])


def log_action(db: Session, action: str, user_id: int | None = None, details: str | None = None) -> None:
    log = models.ActivityLog(action=action, user_id=user_id, details=details)
    db.add(log)


@router.post("/register", response_model=UserOut)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    # For simplicity, allow open registration only if no users exist; otherwise admin-only via future RBAC
    existing_count = db.query(models.User).count()
    if existing_count > 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registration disabled")

    if db.query(models.User).filter(
        (models.User.username == payload.username) | (models.User.email == payload.email)
    ).first():
        raise HTTPException(status_code=400, detail="Username or email already exists")

    user = models.User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    # assign admin role on first user
    admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
    if admin_role:
        user.roles.append(admin_role)
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, "register", user.id, f"User {user.username} registered")
    db.commit()
    return user


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenOut:
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User inactive")

    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    log_action(db, "login", user.id, "User login")
    db.commit()
    return TokenOut(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenOut)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenOut:
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = data.get("sub")
    user = db.get(models.User, int(user_id)) if user_id is not None else None
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid user")
    access = create_access_token(str(user.id
    ))
    refresh = create_refresh_token(str(user.id))
    return TokenOut(access_token=access, refresh_token=refresh)


@router.post("/token", response_model=TokenOut)
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenOut:
    """
    OAuth2 password flow-compatible endpoint for Swagger UI.
    Accepts form fields: username, password.
    """
    user = db.query(models.User).filter(models.User.username == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User inactive")
    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    return TokenOut(access_token=access, refresh_token=refresh)



from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List
from os import getenv

from .db import get_db
from . import models
from .security import decode_token
from .sessions import get_access_from_cookies

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    # Try to get token from Authorization header first, then from cookies
    auth_token = token
    if not auth_token:
        auth_token = get_access_from_cookies(request)
    
    if not auth_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    data = decode_token(auth_token)
    if not data or data.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = data.get("sub")
    user = db.get(models.User, int(user_id)) if user_id is not None else None
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
    return user


def require_roles(required: List[str]):
    def _inner(user: models.User = Depends(get_current_user)) -> models.User:
        user_role_names = {r.name for r in user.roles}
        if not any(role in user_role_names for role in required):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _inner


def require_ingest_writer(request: Request, db: Session = Depends(get_db)) -> models.User | None:
    """
    Allow ingest calls from either:
    - a user JWT with admin/technician role
    - a static device token configured via AMS_INGEST_DEVICE_TOKEN
    """
    auth_header = request.headers.get("authorization", "")
    bearer = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else None
    device_header = request.headers.get("x-device-token")
    provided_device_token = device_header or bearer
    expected_device_token = getenv("AMS_INGEST_DEVICE_TOKEN", "").strip()

    if expected_device_token and provided_device_token and provided_device_token == expected_device_token:
        return None

    if not bearer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing ingest credentials")

    data = decode_token(bearer)
    if not data or data.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ingest token")
    user_id = data.get("sub")
    user = db.get(models.User, int(user_id)) if user_id is not None else None
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
    role_names = {r.name for r in user.roles}
    if not ({"admin", "technician"} & role_names):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return user


def current_user_from_cookie(request: Request, db: Session = Depends(get_db)) -> models.User:
    """UI helper: read access token from cookies, validate, return user."""
    raw = get_access_from_cookies(request)
    data = decode_token(raw or "")
    if not data or data.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user_id = data.get("sub")
    user = db.get(models.User, int(user_id)) if user_id is not None else None
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


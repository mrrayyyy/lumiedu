from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

ROLE_ADMIN = "admin"
ROLE_TEACHER = "teacher"
ROLE_STUDENT = "student"
ROLE_PARENT = "parent"
ALL_ROLES: tuple[str, ...] = (ROLE_ADMIN, ROLE_TEACHER, ROLE_STUDENT, ROLE_PARENT)


@dataclass(frozen=True)
class CurrentUser:
    email: str
    role: str
    full_name: str = ""

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    def has_role(self, *roles: str) -> bool:
        return self.role in roles


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return f"{salt}${digest.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, expected = hashed_password.split("$", 1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 120000
    ).hex()
    return hmac.compare_digest(digest, expected)


def create_access_token(
    subject: str,
    role: str = ROLE_ADMIN,
    full_name: str = "",
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "role": role,
        "name": full_name,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if not payload.get("sub"):
            raise credentials_exception
        return payload
    except JWTError as exc:
        raise credentials_exception from exc


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    if settings.auth_disabled:
        return CurrentUser(
            email=settings.bootstrap_admin_email,
            role=ROLE_ADMIN,
            full_name="Bootstrap Admin",
        )
    payload = decode_access_token(token)
    return CurrentUser(
        email=str(payload["sub"]),
        role=str(payload.get("role", ROLE_ADMIN)),
        full_name=str(payload.get("name", "")),
    )


def get_current_user_email(user: CurrentUser = Depends(get_current_user)) -> str:
    return user.email


def require_roles(*allowed: str):
    allowed_set = set(allowed)

    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not allowed for this action",
            )
        return user

    return dependency

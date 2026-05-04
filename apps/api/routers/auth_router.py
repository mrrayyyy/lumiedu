from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from auth import (
    CurrentUser,
    ROLE_ADMIN,
    create_access_token,
    get_current_user,
    verify_password,
)
from config import settings
from core.rate_limit import check_rate_limit
from repos.user_repo import get_user
from schemas import LoginRequest, TokenResponse, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request) -> TokenResponse:
    client_host = request.client.host if request.client else "unknown"
    await check_rate_limit(
        key=f"ratelimit:login:{payload.email}:{client_host}",
        limit=settings.login_rate_limit_attempts,
        window_seconds=settings.login_rate_limit_window_seconds,
        detail="Too many login attempts. Please try again later.",
    )

    if settings.auth_disabled:
        admin_email = settings.bootstrap_admin_email
        return TokenResponse(
            access_token=create_access_token(admin_email, ROLE_ADMIN, "Bootstrap Admin"),
            email=admin_email,
            role=ROLE_ADMIN,
            full_name="Bootstrap Admin",
        )

    user = await get_user(payload.email)
    if user is None or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    if not verify_password(payload.password, str(user["password_hash"])):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    role = str(user["role"])
    full_name = str(user["full_name"])
    return TokenResponse(
        access_token=create_access_token(payload.email, role, full_name),
        email=payload.email,
        role=role,
        full_name=full_name,
    )


@router.get("/me", response_model=UserResponse)
async def me(current: CurrentUser = Depends(get_current_user)) -> UserResponse:
    user = await get_user(current.email)
    if user is None:
        return UserResponse(
            email=current.email,
            role=current.role,
            full_name=current.full_name,
        )
    return UserResponse(
        email=str(user["email"]),
        role=str(user["role"]),
        full_name=str(user["full_name"]),
        grade_level=(str(user["grade_level"]) if user["grade_level"] else None),
        is_active=bool(user["is_active"]),
    )

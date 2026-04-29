from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status

from auth import create_access_token, verify_password
from config import settings
from core.rate_limit import check_rate_limit
from repos.user_repo import get_user_credentials
from schemas import LoginRequest, TokenResponse

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
        return TokenResponse(access_token=create_access_token(settings.bootstrap_admin_email))

    credentials = await get_user_credentials(payload.email)
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    _, password_hash = credentials
    if not verify_password(payload.password, password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return TokenResponse(access_token=create_access_token(payload.email))

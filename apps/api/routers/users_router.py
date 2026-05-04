from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from auth import CurrentUser, ROLE_ADMIN, hash_password, require_roles
from repos.user_repo import (
    create_user,
    delete_user,
    get_user,
    list_users,
    update_user,
)
from schemas import (
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _to_response(user: dict[str, object]) -> UserResponse:
    return UserResponse(
        email=str(user["email"]),
        role=str(user["role"]),
        full_name=str(user["full_name"]),
        grade_level=(str(user["grade_level"]) if user["grade_level"] else None),
        is_active=bool(user["is_active"]),
    )


@router.get("", response_model=UserListResponse)
async def list_all_users(
    role: str | None = None,
    _: CurrentUser = Depends(require_roles(ROLE_ADMIN)),
) -> UserListResponse:
    users = await list_users(role=role)
    return UserListResponse(
        users=[_to_response(u) for u in users],
        total=len(users),
    )


@router.post("", response_model=UserResponse, status_code=201)
async def create_new_user(
    payload: UserCreateRequest,
    _: CurrentUser = Depends(require_roles(ROLE_ADMIN)),
) -> UserResponse:
    if await get_user(payload.email):
        raise HTTPException(status_code=409, detail="Email already exists")
    ok = await create_user(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        full_name=payload.full_name,
        grade_level=payload.grade_level,
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to create user")
    user = await get_user(payload.email)
    if user is None:
        raise HTTPException(status_code=500, detail="Failed to fetch new user")
    return _to_response(user)


@router.get("/{email}", response_model=UserResponse)
async def get_user_by_email(
    email: str,
    _: CurrentUser = Depends(require_roles(ROLE_ADMIN)),
) -> UserResponse:
    user = await get_user(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_response(user)


@router.patch("/{email}", response_model=UserResponse)
async def update_existing_user(
    email: str,
    payload: UserUpdateRequest,
    _: CurrentUser = Depends(require_roles(ROLE_ADMIN)),
) -> UserResponse:
    user = await get_user(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    password_hash = hash_password(payload.password) if payload.password else None
    ok = await update_user(
        email=email,
        role=payload.role,
        full_name=payload.full_name,
        grade_level=payload.grade_level,
        is_active=payload.is_active,
        password_hash=password_hash,
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to update user")
    updated = await get_user(email)
    if updated is None:
        raise HTTPException(status_code=500, detail="Failed to fetch updated user")
    return _to_response(updated)


@router.delete("/{email}", status_code=204)
async def remove_user(
    email: str,
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN)),
) -> None:
    if email == current.email:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user = await get_user(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not await delete_user(email):
        raise HTTPException(status_code=500, detail="Failed to delete user")

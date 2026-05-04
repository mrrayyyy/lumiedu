from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from auth import CurrentUser, ROLE_ADMIN, ROLE_PARENT, require_roles
from repos.parent_repo import link_parent_child, list_children, unlink_parent_child
from repos.user_repo import get_user
from schemas import ParentChildRequest, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/parents", tags=["parents"])


def _user_to_response(u: dict[str, object]) -> UserResponse:
    return UserResponse(
        email=str(u["email"]),
        role=str(u["role"]),
        full_name=str(u["full_name"]),
        grade_level=(str(u["grade_level"]) if u["grade_level"] else None),
        is_active=bool(u["is_active"]),
    )


@router.get("/me/children", response_model=list[UserResponse])
async def list_my_children(
    current: CurrentUser = Depends(require_roles(ROLE_PARENT)),
) -> list[UserResponse]:
    rows = await list_children(current.email)
    return [_user_to_response(r) for r in rows]


@router.post("/links", response_model=list[UserResponse], status_code=201)
async def link_parent(
    payload: ParentChildRequest,
    _: CurrentUser = Depends(require_roles(ROLE_ADMIN)),
) -> list[UserResponse]:
    parent = await get_user(payload.parent_email)
    if parent is None or parent["role"] != ROLE_PARENT:
        raise HTTPException(status_code=400, detail="Parent email is invalid")
    child = await get_user(payload.child_email)
    if child is None or child["role"] != "student":
        raise HTTPException(status_code=400, detail="Child must be a student account")
    if not await link_parent_child(payload.parent_email, payload.child_email):
        raise HTTPException(status_code=500, detail="Failed to link parent and child")
    rows = await list_children(payload.parent_email)
    return [_user_to_response(r) for r in rows]


@router.delete("/links", status_code=204)
async def unlink_parent(
    payload: ParentChildRequest,
    _: CurrentUser = Depends(require_roles(ROLE_ADMIN)),
) -> None:
    if not await unlink_parent_child(payload.parent_email, payload.child_email):
        raise HTTPException(status_code=500, detail="Failed to unlink parent and child")

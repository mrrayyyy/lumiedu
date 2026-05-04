from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from auth import CurrentUser, ROLE_STUDENT, require_roles
from repos.assignment_repo import list_assignments_for_student
from schemas import AssignmentResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/assignments", tags=["assignments"])


@router.get("/me", response_model=list[AssignmentResponse])
async def list_my_assignments(
    current: CurrentUser = Depends(require_roles(ROLE_STUDENT)),
) -> list[AssignmentResponse]:
    rows = await list_assignments_for_student(current.email)
    return [
        AssignmentResponse(
            assignment_id=str(r["assignment_id"]),
            class_id=str(r["class_id"]),
            class_name=str(r.get("class_name", "")),
            lesson_topic=str(r["lesson_topic"]),
            description=str(r.get("description", "")),
            due_at=r.get("due_at"),  # type: ignore[arg-type]
            created_at=r["created_at"],  # type: ignore[arg-type]
        )
        for r in rows
    ]

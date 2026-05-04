from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from auth import (
    CurrentUser,
    ROLE_ADMIN,
    ROLE_PARENT,
    ROLE_STUDENT,
    ROLE_TEACHER,
    get_current_user,
)
from repos.class_repo import teacher_can_access_student
from repos.parent_repo import is_parent_of
from repos.progress_repo import get_learner_progress
from repos.session_repo import get_sessions_by_learner
from schemas import ProgressResponse, SessionResponse

router = APIRouter(prefix="/api/v1/progress", tags=["progress"])


async def _ensure_can_view(current: CurrentUser, learner_id: str) -> None:
    if current.role == ROLE_ADMIN:
        return
    if current.role == ROLE_STUDENT and learner_id == current.email:
        return
    if current.role == ROLE_TEACHER:
        if learner_id == current.email:
            return
        if await teacher_can_access_student(current.email, learner_id):
            return
    if current.role == ROLE_PARENT and await is_parent_of(current.email, learner_id):
        return
    raise HTTPException(status_code=403, detail="Not allowed to view this learner's progress")


@router.get("/{learner_id}", response_model=ProgressResponse)
async def get_progress(
    learner_id: str,
    current: CurrentUser = Depends(get_current_user),
) -> ProgressResponse:
    await _ensure_can_view(current, learner_id)
    progress_data = await get_learner_progress(learner_id)
    sessions_rows = await get_sessions_by_learner(learner_id)
    recent = [
        SessionResponse(
            session_id=str(r["session_id"]),
            learner_id=str(r["learner_id"]),
            lesson_topic=str(r["lesson_topic"]),
            status=str(r["status"]),
            created_at=r["created_at"],
        )
        for r in sessions_rows[:10]
    ]
    return ProgressResponse(
        learner_id=learner_id,
        total_sessions=int(progress_data["total_sessions"]),
        total_turns=int(progress_data["total_turns"]),
        avg_latency_ms=0,
        topics_studied=list(progress_data["topics_studied"]),
        recent_sessions=recent,
    )

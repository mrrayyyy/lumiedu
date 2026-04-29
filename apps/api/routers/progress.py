from __future__ import annotations

from fastapi import APIRouter, Depends

from auth import get_current_user_email
from repos.progress_repo import get_learner_progress
from repos.session_repo import get_sessions_by_learner
from schemas import ProgressResponse, SessionResponse

router = APIRouter(prefix="/api/v1/progress", tags=["progress"])


@router.get("/{learner_id}", response_model=ProgressResponse)
async def get_progress(
    learner_id: str,
    _user_email: str = Depends(get_current_user_email),
) -> ProgressResponse:
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

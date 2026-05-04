from __future__ import annotations

import logging

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
from repos.memory_repo import (
    get_all_memories,
    get_recent_memories,
    get_skill_assessments,
    get_student_profile,
    upsert_student_profile,
)
from repos.parent_repo import is_parent_of
from schemas import (
    LearningMemoryResponse,
    SkillAssessmentResponse,
    StudentProfileResponse,
    StudentProfileUpdateRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


async def _can_access_student(current: CurrentUser, student_email: str) -> bool:
    if current.role == ROLE_ADMIN:
        return True
    if current.role == ROLE_STUDENT and current.email == student_email:
        return True
    if current.role == ROLE_TEACHER:
        return await teacher_can_access_student(current.email, student_email)
    if current.role == ROLE_PARENT:
        return await is_parent_of(current.email, student_email)
    return False


@router.get("/profile/{student_email}", response_model=StudentProfileResponse)
async def get_profile(
    student_email: str,
    current: CurrentUser = Depends(get_current_user),
) -> StudentProfileResponse:
    if not await _can_access_student(current, student_email):
        raise HTTPException(status_code=403, detail="Cannot access this student's profile")

    profile = await get_student_profile(student_email)
    if not profile:
        return StudentProfileResponse(
            student_email=student_email,
            learning_style="balanced",
            difficulty_level="medium",
            preferred_language="vi",
            strengths="[]",
            weaknesses="[]",
            notes="",
            updated_at=None,  # type: ignore[arg-type]
        )

    return StudentProfileResponse(
        student_email=str(profile["student_email"]),
        learning_style=str(profile["learning_style"]),
        difficulty_level=str(profile["difficulty_level"]),
        preferred_language=str(profile["preferred_language"]),
        strengths=str(profile["strengths"]),
        weaknesses=str(profile["weaknesses"]),
        notes=str(profile["notes"]),
        updated_at=profile["updated_at"],  # type: ignore[arg-type]
    )


@router.put("/profile/{student_email}", response_model=StudentProfileResponse)
async def update_profile(
    student_email: str,
    payload: StudentProfileUpdateRequest,
    current: CurrentUser = Depends(get_current_user),
) -> StudentProfileResponse:
    if current.role not in (ROLE_ADMIN, ROLE_TEACHER):
        if current.role != ROLE_STUDENT or current.email != student_email:
            raise HTTPException(status_code=403, detail="Cannot update this profile")

    existing = await get_student_profile(student_email)
    ls = payload.learning_style or (existing["learning_style"] if existing else "balanced")
    dl = payload.difficulty_level or (existing["difficulty_level"] if existing else "medium")
    strengths = payload.strengths if payload.strengths is not None else (existing["strengths"] if existing else "[]")
    weaknesses = payload.weaknesses if payload.weaknesses is not None else (existing["weaknesses"] if existing else "[]")
    notes = payload.notes if payload.notes is not None else (existing["notes"] if existing else "")

    success = await upsert_student_profile(
        student_email=student_email,
        learning_style=str(ls),
        difficulty_level=str(dl),
        strengths=str(strengths),
        weaknesses=str(weaknesses),
        notes=str(notes),
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update profile")

    return await get_profile(student_email, current)


@router.get("/memories/{student_email}", response_model=list[LearningMemoryResponse])
async def list_memories(
    student_email: str,
    current: CurrentUser = Depends(get_current_user),
) -> list[LearningMemoryResponse]:
    if not await _can_access_student(current, student_email):
        raise HTTPException(status_code=403, detail="Cannot access this student's memories")

    memories = await get_all_memories(student_email)
    return [
        LearningMemoryResponse(
            memory_id=int(m["memory_id"]),
            student_email=str(m["student_email"]),
            session_id=str(m["session_id"]),
            summary=str(m["summary"]),
            topics_covered=str(m["topics_covered"]),
            mistakes_made=str(m["mistakes_made"]),
            mastery_score=float(m["mastery_score"]),
            created_at=m["created_at"],  # type: ignore[arg-type]
        )
        for m in memories
    ]


@router.get("/skills/{student_email}", response_model=list[SkillAssessmentResponse])
async def list_skills(
    student_email: str,
    current: CurrentUser = Depends(get_current_user),
) -> list[SkillAssessmentResponse]:
    if not await _can_access_student(current, student_email):
        raise HTTPException(status_code=403, detail="Cannot access this student's skills")

    skills = await get_skill_assessments(student_email)
    return [
        SkillAssessmentResponse(
            id=int(s["id"]),
            student_email=str(s["student_email"]),
            topic=str(s["topic"]),
            sub_skill=str(s["sub_skill"]),
            correct_count=int(s["correct_count"]),
            total_attempts=int(s["total_attempts"]),
            mastery_rate=round(int(s["correct_count"]) / max(int(s["total_attempts"]), 1), 2),
            last_assessed_at=s["last_assessed_at"],  # type: ignore[arg-type]
        )
        for s in skills
    ]

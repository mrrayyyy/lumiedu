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
    require_roles,
)
from repos.assignment_repo import (
    create_assignment,
    delete_assignment,
    list_assignments_by_class,
)
from repos.class_repo import (
    add_member,
    create_class,
    get_class,
    is_member,
    list_all_classes,
    list_classes_by_student,
    list_classes_by_teacher,
    list_members,
    list_students_for_teacher,
    remove_member,
)
from repos.parent_repo import list_children
from repos.user_repo import get_user
from schemas import (
    AssignmentCreateRequest,
    AssignmentResponse,
    ClassCreateRequest,
    ClassDetailResponse,
    ClassMemberAddRequest,
    ClassResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/classes", tags=["classes"])


def _class_to_response(c: dict[str, object]) -> ClassResponse:
    return ClassResponse(
        class_id=str(c["class_id"]),
        name=str(c["name"]),
        description=str(c["description"]),
        teacher_email=str(c["teacher_email"]),
        teacher_name=str(c["teacher_name"]),
        member_count=int(c["member_count"]),
        created_at=c["created_at"],  # type: ignore[arg-type]
    )


def _user_to_response(u: dict[str, object]) -> UserResponse:
    return UserResponse(
        email=str(u["email"]),
        role=str(u["role"]),
        full_name=str(u["full_name"]),
        grade_level=(str(u["grade_level"]) if u["grade_level"] else None),
        is_active=bool(u["is_active"]),
    )


def _assignment_to_response(a: dict[str, object]) -> AssignmentResponse:
    return AssignmentResponse(
        assignment_id=str(a["assignment_id"]),
        class_id=str(a["class_id"]),
        class_name=str(a.get("class_name", "")),
        lesson_topic=str(a["lesson_topic"]),
        description=str(a.get("description", "")),
        due_at=a.get("due_at"),  # type: ignore[arg-type]
        created_at=a["created_at"],  # type: ignore[arg-type]
    )


async def _can_view_class(current: CurrentUser, klass: dict[str, object]) -> bool:
    if current.role == ROLE_ADMIN:
        return True
    if current.role == ROLE_TEACHER and current.email == klass["teacher_email"]:
        return True
    if current.role == ROLE_STUDENT and await is_member(str(klass["class_id"]), current.email):
        return True
    if current.role == ROLE_PARENT:
        children = await list_children(current.email)
        for child in children:
            if await is_member(str(klass["class_id"]), str(child["email"])):
                return True
    return False


async def _can_manage_class(current: CurrentUser, klass: dict[str, object]) -> bool:
    if current.role == ROLE_ADMIN:
        return True
    if current.role == ROLE_TEACHER and current.email == klass["teacher_email"]:
        return True
    return False


@router.get("", response_model=list[ClassResponse])
async def list_classes(
    current: CurrentUser = Depends(get_current_user),
) -> list[ClassResponse]:
    if current.role == ROLE_ADMIN:
        rows = await list_all_classes()
    elif current.role == ROLE_TEACHER:
        rows = await list_classes_by_teacher(current.email)
    elif current.role == ROLE_STUDENT:
        rows = await list_classes_by_student(current.email)
    elif current.role == ROLE_PARENT:
        rows = []
        seen: set[str] = set()
        for child in await list_children(current.email):
            for c in await list_classes_by_student(str(child["email"])):
                cid = str(c["class_id"])
                if cid in seen:
                    continue
                seen.add(cid)
                rows.append(c)
    else:
        rows = []
    return [_class_to_response(r) for r in rows]


@router.post("", response_model=ClassResponse, status_code=201)
async def create_new_class(
    payload: ClassCreateRequest,
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> ClassResponse:
    teacher_email = payload.teacher_email or current.email
    if current.role == ROLE_TEACHER and teacher_email != current.email:
        raise HTTPException(
            status_code=403,
            detail="Teachers can only create classes for themselves",
        )
    teacher = await get_user(teacher_email)
    if teacher is None or teacher["role"] != ROLE_TEACHER:
        raise HTTPException(status_code=400, detail="Teacher email is invalid")
    class_id = await create_class(payload.name, payload.description, teacher_email)
    if class_id is None:
        raise HTTPException(status_code=500, detail="Failed to create class")
    klass = await get_class(class_id)
    if klass is None:
        raise HTTPException(status_code=500, detail="Failed to fetch new class")
    return _class_to_response(klass)


@router.get("/teacher/students", response_model=list[UserResponse])
async def teacher_students(
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> list[UserResponse]:
    rows = await list_students_for_teacher(current.email)
    return [_user_to_response(r) for r in rows]


@router.get("/{class_id}", response_model=ClassDetailResponse)
async def get_class_detail(
    class_id: str,
    current: CurrentUser = Depends(get_current_user),
) -> ClassDetailResponse:
    klass = await get_class(class_id)
    if klass is None:
        raise HTTPException(status_code=404, detail="Class not found")
    if not await _can_view_class(current, klass):
        raise HTTPException(status_code=403, detail="Not allowed to view this class")
    members_rows = await list_members(class_id)
    assignments_rows = await list_assignments_by_class(class_id)
    base = _class_to_response(klass)
    return ClassDetailResponse(
        **base.model_dump(),
        members=[_user_to_response(m) for m in members_rows],
        assignments=[_assignment_to_response(a) for a in assignments_rows],
    )


@router.post("/{class_id}/members", response_model=list[UserResponse])
async def add_class_member(
    class_id: str,
    payload: ClassMemberAddRequest,
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> list[UserResponse]:
    klass = await get_class(class_id)
    if klass is None:
        raise HTTPException(status_code=404, detail="Class not found")
    if not await _can_manage_class(current, klass):
        raise HTTPException(status_code=403, detail="Not allowed to manage this class")
    student = await get_user(payload.student_email)
    if student is None or student["role"] != ROLE_STUDENT:
        raise HTTPException(status_code=400, detail="Student email is invalid")
    if not await add_member(class_id, payload.student_email):
        raise HTTPException(status_code=500, detail="Failed to add member")
    members_rows = await list_members(class_id)
    return [_user_to_response(m) for m in members_rows]


@router.delete("/{class_id}/members/{student_email}", status_code=204)
async def remove_class_member(
    class_id: str,
    student_email: str,
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> None:
    klass = await get_class(class_id)
    if klass is None:
        raise HTTPException(status_code=404, detail="Class not found")
    if not await _can_manage_class(current, klass):
        raise HTTPException(status_code=403, detail="Not allowed to manage this class")
    if not await remove_member(class_id, student_email):
        raise HTTPException(status_code=500, detail="Failed to remove member")


@router.get("/{class_id}/assignments", response_model=list[AssignmentResponse])
async def list_class_assignments(
    class_id: str,
    current: CurrentUser = Depends(get_current_user),
) -> list[AssignmentResponse]:
    klass = await get_class(class_id)
    if klass is None:
        raise HTTPException(status_code=404, detail="Class not found")
    if not await _can_view_class(current, klass):
        raise HTTPException(status_code=403, detail="Not allowed to view this class")
    rows = await list_assignments_by_class(class_id)
    return [_assignment_to_response(r) for r in rows]


@router.post("/{class_id}/assignments", response_model=AssignmentResponse, status_code=201)
async def create_class_assignment(
    class_id: str,
    payload: AssignmentCreateRequest,
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> AssignmentResponse:
    klass = await get_class(class_id)
    if klass is None:
        raise HTTPException(status_code=404, detail="Class not found")
    if not await _can_manage_class(current, klass):
        raise HTTPException(status_code=403, detail="Not allowed to manage this class")
    assignment_id = await create_assignment(
        class_id=class_id,
        lesson_topic=payload.lesson_topic,
        description=payload.description,
        due_at=payload.due_at,
    )
    if assignment_id is None:
        raise HTTPException(status_code=500, detail="Failed to create assignment")
    rows = await list_assignments_by_class(class_id)
    for row in rows:
        if str(row["assignment_id"]) == assignment_id:
            return _assignment_to_response(row)
    raise HTTPException(status_code=500, detail="Failed to fetch new assignment")


@router.delete("/{class_id}/assignments/{assignment_id}", status_code=204)
async def remove_assignment(
    class_id: str,
    assignment_id: str,
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> None:
    klass = await get_class(class_id)
    if klass is None:
        raise HTTPException(status_code=404, detail="Class not found")
    if not await _can_manage_class(current, klass):
        raise HTTPException(status_code=403, detail="Not allowed to manage this class")
    if not await delete_assignment(assignment_id):
        raise HTTPException(status_code=500, detail="Failed to delete assignment")

from __future__ import annotations

import logging
from datetime import datetime
from uuid import uuid4

from sqlalchemy import text

from core.database import engine

logger = logging.getLogger(__name__)


def _row_to_assignment(row: object) -> dict[str, object]:
    return {
        "assignment_id": str(row[0]),
        "class_id": str(row[1]),
        "class_name": str(row[2] or ""),
        "lesson_topic": str(row[3]),
        "description": str(row[4] or ""),
        "due_at": row[5],
        "created_at": row[6],
    }


_ASSIGNMENT_BASE_SQL = (
    "SELECT a.assignment_id, a.class_id, COALESCE(c.name, '') AS class_name, "
    "a.lesson_topic, a.description, a.due_at, a.created_at "
    "FROM lesson_assignments a "
    "LEFT JOIN classes c ON c.class_id = a.class_id"
)


async def create_assignment(
    class_id: str,
    lesson_topic: str,
    description: str,
    due_at: datetime | None,
) -> str | None:
    assignment_id = str(uuid4())
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO lesson_assignments (assignment_id, class_id, lesson_topic, description, due_at) "
                    "VALUES (:assignment_id, :class_id, :lesson_topic, :description, :due_at)"
                ),
                {
                    "assignment_id": assignment_id,
                    "class_id": class_id,
                    "lesson_topic": lesson_topic,
                    "description": description,
                    "due_at": due_at,
                },
            )
        return assignment_id
    except Exception as exc:
        logger.warning("create_assignment_failed", extra={"error": str(exc)})
        return None


async def list_assignments_by_class(class_id: str) -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    f"{_ASSIGNMENT_BASE_SQL} WHERE a.class_id = :class_id "
                    "ORDER BY a.created_at DESC"
                ),
                {"class_id": class_id},
            )
            return [_row_to_assignment(r) for r in result.fetchall()]
    except Exception as exc:
        logger.warning("list_assignments_by_class_failed", extra={"error": str(exc)})
        return []


async def list_assignments_for_student(student_email: str) -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    f"{_ASSIGNMENT_BASE_SQL} "
                    "JOIN class_members cm ON cm.class_id = a.class_id "
                    "WHERE cm.student_email = :student_email "
                    "ORDER BY a.created_at DESC"
                ),
                {"student_email": student_email},
            )
            return [_row_to_assignment(r) for r in result.fetchall()]
    except Exception as exc:
        logger.warning("list_assignments_for_student_failed", extra={"error": str(exc)})
        return []


async def delete_assignment(assignment_id: str) -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM lesson_assignments WHERE assignment_id = :assignment_id"),
                {"assignment_id": assignment_id},
            )
        return True
    except Exception as exc:
        logger.warning("delete_assignment_failed", extra={"error": str(exc)})
        return False

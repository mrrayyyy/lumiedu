from __future__ import annotations

import logging
from uuid import uuid4

from sqlalchemy import text

from core.database import engine

logger = logging.getLogger(__name__)


def _row_to_class(row: object) -> dict[str, object]:
    return {
        "class_id": str(row[0]),
        "name": str(row[1]),
        "description": str(row[2] or ""),
        "teacher_email": str(row[3]),
        "teacher_name": str(row[4] or ""),
        "member_count": int(row[5] or 0),
        "created_at": row[6],
    }


_CLASS_LIST_SQL = (
    "SELECT c.class_id, c.name, c.description, c.teacher_email, "
    "COALESCE(u.full_name, '') AS teacher_name, "
    "(SELECT COUNT(*) FROM class_members m WHERE m.class_id = c.class_id) AS member_count, "
    "c.created_at "
    "FROM classes c "
    "LEFT JOIN auth_users u ON u.email = c.teacher_email"
)


async def create_class(name: str, description: str, teacher_email: str) -> str | None:
    class_id = str(uuid4())
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO classes (class_id, name, description, teacher_email) "
                    "VALUES (:class_id, :name, :description, :teacher_email)"
                ),
                {
                    "class_id": class_id,
                    "name": name,
                    "description": description,
                    "teacher_email": teacher_email,
                },
            )
        return class_id
    except Exception as exc:
        logger.warning("create_class_failed", extra={"error": str(exc)})
        return None


async def get_class(class_id: str) -> dict[str, object] | None:
    try:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(f"{_CLASS_LIST_SQL} WHERE c.class_id = :class_id"),
                    {"class_id": class_id},
                )
            ).first()
            if not row:
                return None
            return _row_to_class(row)
    except Exception as exc:
        logger.warning("get_class_failed", extra={"class_id": class_id, "error": str(exc)})
        return None


async def list_all_classes() -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(f"{_CLASS_LIST_SQL} ORDER BY c.created_at DESC")
            )
            return [_row_to_class(r) for r in result.fetchall()]
    except Exception as exc:
        logger.warning("list_all_classes_failed", extra={"error": str(exc)})
        return []


async def list_classes_by_teacher(teacher_email: str) -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    f"{_CLASS_LIST_SQL} WHERE c.teacher_email = :teacher_email "
                    "ORDER BY c.created_at DESC"
                ),
                {"teacher_email": teacher_email},
            )
            return [_row_to_class(r) for r in result.fetchall()]
    except Exception as exc:
        logger.warning(
            "list_classes_by_teacher_failed", extra={"teacher_email": teacher_email, "error": str(exc)}
        )
        return []


async def list_classes_by_student(student_email: str) -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    f"{_CLASS_LIST_SQL} JOIN class_members cm ON cm.class_id = c.class_id "
                    "WHERE cm.student_email = :student_email "
                    "ORDER BY c.created_at DESC"
                ),
                {"student_email": student_email},
            )
            return [_row_to_class(r) for r in result.fetchall()]
    except Exception as exc:
        logger.warning(
            "list_classes_by_student_failed",
            extra={"student_email": student_email, "error": str(exc)},
        )
        return []


async def add_member(class_id: str, student_email: str) -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO class_members (class_id, student_email) "
                    "VALUES (:class_id, :student_email) "
                    "ON CONFLICT DO NOTHING"
                ),
                {"class_id": class_id, "student_email": student_email},
            )
        return True
    except Exception as exc:
        logger.warning(
            "add_member_failed",
            extra={"class_id": class_id, "student_email": student_email, "error": str(exc)},
        )
        return False


async def remove_member(class_id: str, student_email: str) -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "DELETE FROM class_members "
                    "WHERE class_id = :class_id AND student_email = :student_email"
                ),
                {"class_id": class_id, "student_email": student_email},
            )
        return True
    except Exception as exc:
        logger.warning("remove_member_failed", extra={"error": str(exc)})
        return False


async def list_members(class_id: str) -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT u.email, u.role, u.full_name, u.grade_level, u.is_active "
                    "FROM class_members m "
                    "JOIN auth_users u ON u.email = m.student_email "
                    "WHERE m.class_id = :class_id "
                    "ORDER BY m.joined_at"
                ),
                {"class_id": class_id},
            )
            return [
                {
                    "email": str(r[0]),
                    "role": str(r[1]),
                    "full_name": str(r[2] or ""),
                    "grade_level": (str(r[3]) if r[3] else None),
                    "is_active": bool(r[4]),
                }
                for r in result.fetchall()
            ]
    except Exception as exc:
        logger.warning("list_members_failed", extra={"class_id": class_id, "error": str(exc)})
        return []


async def is_member(class_id: str, student_email: str) -> bool:
    try:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(
                        "SELECT 1 FROM class_members "
                        "WHERE class_id = :class_id AND student_email = :student_email"
                    ),
                    {"class_id": class_id, "student_email": student_email},
                )
            ).first()
            return row is not None
    except Exception as exc:
        logger.warning("is_member_failed", extra={"error": str(exc)})
        return False


async def list_students_for_teacher(teacher_email: str) -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT DISTINCT u.email, u.role, u.full_name, u.grade_level, u.is_active "
                    "FROM class_members m "
                    "JOIN classes c ON c.class_id = m.class_id "
                    "JOIN auth_users u ON u.email = m.student_email "
                    "WHERE c.teacher_email = :teacher_email "
                    "ORDER BY u.full_name"
                ),
                {"teacher_email": teacher_email},
            )
            return [
                {
                    "email": str(r[0]),
                    "role": str(r[1]),
                    "full_name": str(r[2] or ""),
                    "grade_level": (str(r[3]) if r[3] else None),
                    "is_active": bool(r[4]),
                }
                for r in result.fetchall()
            ]
    except Exception as exc:
        logger.warning("list_students_for_teacher_failed", extra={"error": str(exc)})
        return []


async def teacher_can_access_student(teacher_email: str, student_email: str) -> bool:
    try:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(
                        "SELECT 1 FROM class_members m "
                        "JOIN classes c ON c.class_id = m.class_id "
                        "WHERE c.teacher_email = :teacher_email "
                        "AND m.student_email = :student_email "
                        "LIMIT 1"
                    ),
                    {"teacher_email": teacher_email, "student_email": student_email},
                )
            ).first()
            return row is not None
    except Exception as exc:
        logger.warning("teacher_can_access_student_failed", extra={"error": str(exc)})
        return False

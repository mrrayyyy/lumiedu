from __future__ import annotations

import logging

from sqlalchemy import text

from core.database import engine

logger = logging.getLogger(__name__)


async def link_parent_child(parent_email: str, child_email: str) -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO parent_children (parent_email, child_email) "
                    "VALUES (:parent_email, :child_email) "
                    "ON CONFLICT DO NOTHING"
                ),
                {"parent_email": parent_email, "child_email": child_email},
            )
        return True
    except Exception as exc:
        logger.warning("link_parent_child_failed", extra={"error": str(exc)})
        return False


async def unlink_parent_child(parent_email: str, child_email: str) -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "DELETE FROM parent_children "
                    "WHERE parent_email = :parent_email AND child_email = :child_email"
                ),
                {"parent_email": parent_email, "child_email": child_email},
            )
        return True
    except Exception as exc:
        logger.warning("unlink_parent_child_failed", extra={"error": str(exc)})
        return False


async def list_children(parent_email: str) -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT u.email, u.role, u.full_name, u.grade_level, u.is_active "
                    "FROM parent_children pc "
                    "JOIN auth_users u ON u.email = pc.child_email "
                    "WHERE pc.parent_email = :parent_email "
                    "ORDER BY u.full_name"
                ),
                {"parent_email": parent_email},
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
        logger.warning("list_children_failed", extra={"error": str(exc)})
        return []


async def is_parent_of(parent_email: str, child_email: str) -> bool:
    try:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(
                        "SELECT 1 FROM parent_children "
                        "WHERE parent_email = :parent_email AND child_email = :child_email"
                    ),
                    {"parent_email": parent_email, "child_email": child_email},
                )
            ).first()
            return row is not None
    except Exception as exc:
        logger.warning("is_parent_of_failed", extra={"error": str(exc)})
        return False

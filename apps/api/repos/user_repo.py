from __future__ import annotations

import logging

from sqlalchemy import text

from core.database import engine

logger = logging.getLogger(__name__)


_USER_COLUMNS = "email, password_hash, role, full_name, grade_level, is_active"


def _row_to_user(row: object) -> dict[str, object]:
    return {
        "email": str(row[0]),
        "password_hash": str(row[1]),
        "role": str(row[2]),
        "full_name": str(row[3] or ""),
        "grade_level": (str(row[4]) if row[4] else None),
        "is_active": bool(row[5]),
    }


async def get_user_credentials(email: str) -> tuple[str, str] | None:
    user = await get_user(email)
    if user is None or not user["is_active"]:
        return None
    return str(user["email"]), str(user["password_hash"])


async def get_user(email: str) -> dict[str, object] | None:
    try:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(f"SELECT {_USER_COLUMNS} FROM auth_users WHERE email = :email"),
                    {"email": email},
                )
            ).first()
            if not row:
                return None
            return _row_to_user(row)
    except Exception as exc:
        logger.warning("get_user_failed", extra={"email": email, "error": str(exc)})
        return None


async def list_users(role: str | None = None) -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            if role:
                result = await conn.execute(
                    text(
                        f"SELECT {_USER_COLUMNS} FROM auth_users WHERE role = :role "
                        "ORDER BY created_at DESC"
                    ),
                    {"role": role},
                )
            else:
                result = await conn.execute(
                    text(f"SELECT {_USER_COLUMNS} FROM auth_users ORDER BY created_at DESC")
                )
            return [_row_to_user(row) for row in result.fetchall()]
    except Exception as exc:
        logger.warning("list_users_failed", extra={"role": role, "error": str(exc)})
        return []


async def create_user(
    email: str,
    password_hash: str,
    role: str,
    full_name: str,
    grade_level: str | None,
) -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO auth_users (email, password_hash, role, full_name, grade_level) "
                    "VALUES (:email, :password_hash, :role, :full_name, :grade_level)"
                ),
                {
                    "email": email,
                    "password_hash": password_hash,
                    "role": role,
                    "full_name": full_name,
                    "grade_level": grade_level,
                },
            )
        return True
    except Exception as exc:
        logger.warning("create_user_failed", extra={"email": email, "error": str(exc)})
        return False


async def update_user(
    email: str,
    role: str | None = None,
    full_name: str | None = None,
    grade_level: str | None = None,
    is_active: bool | None = None,
    password_hash: str | None = None,
) -> bool:
    fields: list[str] = []
    params: dict[str, object] = {"email": email}
    if role is not None:
        fields.append("role = :role")
        params["role"] = role
    if full_name is not None:
        fields.append("full_name = :full_name")
        params["full_name"] = full_name
    if grade_level is not None:
        fields.append("grade_level = :grade_level")
        params["grade_level"] = grade_level
    if is_active is not None:
        fields.append("is_active = :is_active")
        params["is_active"] = is_active
    if password_hash is not None:
        fields.append("password_hash = :password_hash")
        params["password_hash"] = password_hash
    if not fields:
        return True
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(f"UPDATE auth_users SET {', '.join(fields)} WHERE email = :email"),
                params,
            )
        return True
    except Exception as exc:
        logger.warning("update_user_failed", extra={"email": email, "error": str(exc)})
        return False


async def delete_user(email: str) -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM auth_users WHERE email = :email"),
                {"email": email},
            )
        return True
    except Exception as exc:
        logger.warning("delete_user_failed", extra={"email": email, "error": str(exc)})
        return False

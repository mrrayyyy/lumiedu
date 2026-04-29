from __future__ import annotations

import logging

from sqlalchemy import text

from core.database import engine

logger = logging.getLogger(__name__)


async def get_user_credentials(email: str) -> tuple[str, str] | None:
    try:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text("SELECT email, password_hash FROM auth_users WHERE email = :email"),
                    {"email": email},
                )
            ).first()
            if not row:
                return None
            return str(row[0]), str(row[1])
    except Exception as exc:
        logger.warning("get_user_credentials_failed", extra={"email": email, "error": str(exc)})
        return None

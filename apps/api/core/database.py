from __future__ import annotations

import logging

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from auth import hash_password
from config import settings

logger = logging.getLogger(__name__)

engine: AsyncEngine = create_async_engine(settings.database_url, echo=False, future=True)
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

_SCHEMA_SQL = [
    """
    CREATE TABLE IF NOT EXISTS learning_sessions (
        session_id TEXT PRIMARY KEY,
        learner_id TEXT NOT NULL,
        lesson_topic TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS auth_users (
        email TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'admin',
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS session_turns (
        turn_id BIGSERIAL PRIMARY KEY,
        session_id TEXT NOT NULL,
        transcript TEXT NOT NULL,
        assistant_response TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """,
]


async def ensure_db_ready() -> None:
    try:
        async with engine.begin() as conn:
            for sql in _SCHEMA_SQL:
                await conn.execute(text(sql))
            await conn.execute(
                text(
                    "INSERT INTO auth_users (email, password_hash, role) "
                    "VALUES (:email, :password_hash, 'admin') "
                    "ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash;"
                ),
                {
                    "email": settings.bootstrap_admin_email,
                    "password_hash": hash_password(settings.bootstrap_admin_password),
                },
            )
    except Exception as exc:
        logger.warning("database_init_failed", extra={"error": str(exc)})


async def close_connections() -> None:
    await redis_client.close()
    await engine.dispose()


async def ping_dependencies() -> dict[str, str]:
    db_status = "ok"
    redis_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "degraded"
    try:
        await redis_client.ping()
    except Exception:
        redis_status = "degraded"
    return {"postgres": db_status, "redis": redis_status}

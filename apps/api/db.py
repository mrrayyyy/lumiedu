from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from redis.asyncio import Redis

from config import settings
from auth import hash_password

logger = logging.getLogger(__name__)

engine: AsyncEngine = create_async_engine(settings.database_url, echo=False, future=True)
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


async def ensure_db_ready() -> None:
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS learning_sessions (
                        session_id TEXT PRIMARY KEY,
                        learner_id TEXT NOT NULL,
                        lesson_topic TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW()
                    );
                    """
                )
            )
            await connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS auth_users (
                        email TEXT PRIMARY KEY,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL DEFAULT 'admin',
                        created_at TIMESTAMP NOT NULL DEFAULT NOW()
                    );
                    """
                )
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO auth_users (email, password_hash, role)
                    VALUES (:email, :password_hash, 'admin')
                    ON CONFLICT (email) DO UPDATE
                    SET password_hash = EXCLUDED.password_hash;
                    """
                ),
                {
                    "email": settings.bootstrap_admin_email,
                    "password_hash": hash_password(settings.bootstrap_admin_password),
                },
            )
            await connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS session_turns (
                        turn_id BIGSERIAL PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        transcript TEXT NOT NULL,
                        assistant_response TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW()
                    );
                    """
                )
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
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        db_status = "degraded"
    try:
        await redis_client.ping()
    except Exception:
        redis_status = "degraded"
    return {"postgres": db_status, "redis": redis_status}


async def save_session(session_id: str, learner_id: str, lesson_topic: str, status: str) -> None:
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    INSERT INTO learning_sessions (session_id, learner_id, lesson_topic, status)
                    VALUES (:session_id, :learner_id, :lesson_topic, :status)
                    ON CONFLICT (session_id) DO UPDATE
                    SET status = EXCLUDED.status;
                    """
                ),
                {
                    "session_id": session_id,
                    "learner_id": learner_id,
                    "lesson_topic": lesson_topic,
                    "status": status,
                },
            )
    except Exception as exc:
        logger.warning("save_session_failed", extra={"session_id": session_id, "error": str(exc)})


async def save_turn(session_id: str, transcript: str, assistant_response: str) -> None:
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    INSERT INTO session_turns (session_id, transcript, assistant_response)
                    VALUES (:session_id, :transcript, :assistant_response);
                    """
                ),
                {
                    "session_id": session_id,
                    "transcript": transcript,
                    "assistant_response": assistant_response,
                },
            )
    except Exception as exc:
        logger.warning("save_turn_failed", extra={"session_id": session_id, "error": str(exc)})


async def get_user_credentials(email: str) -> tuple[str, str] | None:
    try:
        async with engine.connect() as connection:
            row = (
                await connection.execute(
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

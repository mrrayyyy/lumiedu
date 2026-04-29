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


async def get_sessions_by_learner(learner_id: str) -> list[dict[str, object]]:
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text(
                    "SELECT session_id, learner_id, lesson_topic, status, created_at "
                    "FROM learning_sessions WHERE learner_id = :learner_id "
                    "ORDER BY created_at DESC LIMIT 50"
                ),
                {"learner_id": learner_id},
            )
            rows = result.fetchall()
            return [
                {
                    "session_id": str(r[0]),
                    "learner_id": str(r[1]),
                    "lesson_topic": str(r[2]),
                    "status": str(r[3]),
                    "created_at": r[4],
                }
                for r in rows
            ]
    except Exception as exc:
        logger.warning("get_sessions_by_learner_failed", extra={"learner_id": learner_id, "error": str(exc)})
        return []


async def get_all_sessions() -> list[dict[str, object]]:
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text(
                    "SELECT session_id, learner_id, lesson_topic, status, created_at "
                    "FROM learning_sessions ORDER BY created_at DESC LIMIT 100"
                )
            )
            rows = result.fetchall()
            return [
                {
                    "session_id": str(r[0]),
                    "learner_id": str(r[1]),
                    "lesson_topic": str(r[2]),
                    "status": str(r[3]),
                    "created_at": r[4],
                }
                for r in rows
            ]
    except Exception as exc:
        logger.warning("get_all_sessions_failed", extra={"error": str(exc)})
        return []


async def update_session_status(session_id: str, new_status: str) -> None:
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE learning_sessions SET status = :status WHERE session_id = :session_id"
                ),
                {"session_id": session_id, "status": new_status},
            )
    except Exception as exc:
        logger.warning("update_session_status_failed", extra={"session_id": session_id, "error": str(exc)})


async def get_turns_by_session(session_id: str) -> list[dict[str, object]]:
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text(
                    "SELECT transcript, assistant_response, created_at "
                    "FROM session_turns WHERE session_id = :session_id "
                    "ORDER BY created_at ASC"
                ),
                {"session_id": session_id},
            )
            rows = result.fetchall()
            return [
                {
                    "transcript": str(r[0]),
                    "assistant_response": str(r[1]),
                    "created_at": r[2],
                }
                for r in rows
            ]
    except Exception as exc:
        logger.warning("get_turns_by_session_failed", extra={"session_id": session_id, "error": str(exc)})
        return []


async def get_learner_progress(learner_id: str) -> dict[str, object]:
    try:
        async with engine.connect() as connection:
            session_result = await connection.execute(
                text(
                    "SELECT COUNT(*), "
                    "ARRAY_AGG(DISTINCT lesson_topic) "
                    "FROM learning_sessions WHERE learner_id = :learner_id"
                ),
                {"learner_id": learner_id},
            )
            session_row = session_result.first()
            total_sessions = int(session_row[0]) if session_row else 0
            topics = list(session_row[1]) if session_row and session_row[1] else []

            turn_result = await connection.execute(
                text(
                    "SELECT COUNT(*) FROM session_turns st "
                    "JOIN learning_sessions ls ON st.session_id = ls.session_id "
                    "WHERE ls.learner_id = :learner_id"
                ),
                {"learner_id": learner_id},
            )
            turn_row = turn_result.first()
            total_turns = int(turn_row[0]) if turn_row else 0

            return {
                "total_sessions": total_sessions,
                "total_turns": total_turns,
                "topics_studied": topics,
            }
    except Exception as exc:
        logger.warning("get_learner_progress_failed", extra={"learner_id": learner_id, "error": str(exc)})
        return {"total_sessions": 0, "total_turns": 0, "topics_studied": []}

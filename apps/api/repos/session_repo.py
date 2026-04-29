from __future__ import annotations

import logging

from sqlalchemy import text

from core.database import engine

logger = logging.getLogger(__name__)


async def save_session(session_id: str, learner_id: str, lesson_topic: str, status: str) -> None:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO learning_sessions (session_id, learner_id, lesson_topic, status) "
                    "VALUES (:session_id, :learner_id, :lesson_topic, :status) "
                    "ON CONFLICT (session_id) DO UPDATE SET status = EXCLUDED.status;"
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
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO session_turns (session_id, transcript, assistant_response) "
                    "VALUES (:session_id, :transcript, :assistant_response);"
                ),
                {
                    "session_id": session_id,
                    "transcript": transcript,
                    "assistant_response": assistant_response,
                },
            )
    except Exception as exc:
        logger.warning("save_turn_failed", extra={"session_id": session_id, "error": str(exc)})


async def get_sessions_by_learner(learner_id: str) -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT session_id, learner_id, lesson_topic, status, created_at "
                    "FROM learning_sessions WHERE learner_id = :learner_id "
                    "ORDER BY created_at DESC LIMIT 50"
                ),
                {"learner_id": learner_id},
            )
            return [
                {
                    "session_id": str(r[0]),
                    "learner_id": str(r[1]),
                    "lesson_topic": str(r[2]),
                    "status": str(r[3]),
                    "created_at": r[4],
                }
                for r in result.fetchall()
            ]
    except Exception as exc:
        logger.warning("get_sessions_by_learner_failed", extra={"learner_id": learner_id, "error": str(exc)})
        return []


async def get_all_sessions() -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT session_id, learner_id, lesson_topic, status, created_at "
                    "FROM learning_sessions ORDER BY created_at DESC LIMIT 100"
                )
            )
            return [
                {
                    "session_id": str(r[0]),
                    "learner_id": str(r[1]),
                    "lesson_topic": str(r[2]),
                    "status": str(r[3]),
                    "created_at": r[4],
                }
                for r in result.fetchall()
            ]
    except Exception as exc:
        logger.warning("get_all_sessions_failed", extra={"error": str(exc)})
        return []


async def update_session_status(session_id: str, new_status: str) -> None:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "UPDATE learning_sessions SET status = :status "
                    "WHERE session_id = :session_id"
                ),
                {"session_id": session_id, "status": new_status},
            )
    except Exception as exc:
        logger.warning(
            "update_session_status_failed",
            extra={"session_id": session_id, "error": str(exc)},
        )


async def get_turns_by_session(session_id: str) -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT transcript, assistant_response, created_at "
                    "FROM session_turns WHERE session_id = :session_id "
                    "ORDER BY created_at ASC"
                ),
                {"session_id": session_id},
            )
            return [
                {
                    "transcript": str(r[0]),
                    "assistant_response": str(r[1]),
                    "created_at": r[2],
                }
                for r in result.fetchall()
            ]
    except Exception as exc:
        logger.warning("get_turns_by_session_failed", extra={"session_id": session_id, "error": str(exc)})
        return []

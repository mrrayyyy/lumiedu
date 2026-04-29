from __future__ import annotations

import logging

from sqlalchemy import text

from core.database import engine

logger = logging.getLogger(__name__)


async def get_learner_progress(learner_id: str) -> dict[str, object]:
    try:
        async with engine.connect() as conn:
            session_result = await conn.execute(
                text(
                    "SELECT COUNT(*), ARRAY_AGG(DISTINCT lesson_topic) "
                    "FROM learning_sessions WHERE learner_id = :learner_id"
                ),
                {"learner_id": learner_id},
            )
            session_row = session_result.first()
            total_sessions = int(session_row[0]) if session_row else 0
            topics = list(session_row[1]) if session_row and session_row[1] else []

            turn_result = await conn.execute(
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

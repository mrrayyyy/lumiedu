from __future__ import annotations

import logging

from sqlalchemy import text

from core.database import engine

logger = logging.getLogger(__name__)


async def get_student_profile(student_email: str) -> dict[str, object] | None:
    try:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(
                        "SELECT student_email, learning_style, difficulty_level, "
                        "preferred_language, strengths, weaknesses, notes, updated_at "
                        "FROM student_profiles WHERE student_email = :email"
                    ),
                    {"email": student_email},
                )
            ).first()
            if not row:
                return None
            return {
                "student_email": str(row[0]),
                "learning_style": str(row[1]),
                "difficulty_level": str(row[2]),
                "preferred_language": str(row[3]),
                "strengths": str(row[4]),
                "weaknesses": str(row[5]),
                "notes": str(row[6]),
                "updated_at": row[7],
            }
    except Exception as exc:
        logger.warning("get_student_profile_failed: %s", exc)
        return None


async def upsert_student_profile(
    student_email: str,
    learning_style: str = "balanced",
    difficulty_level: str = "medium",
    strengths: str = "[]",
    weaknesses: str = "[]",
    notes: str = "",
) -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO student_profiles "
                    "(student_email, learning_style, difficulty_level, strengths, weaknesses, notes, updated_at) "
                    "VALUES (:email, :ls, :dl, :strengths, :weaknesses, :notes, NOW()) "
                    "ON CONFLICT (student_email) DO UPDATE SET "
                    "learning_style = EXCLUDED.learning_style, "
                    "difficulty_level = EXCLUDED.difficulty_level, "
                    "strengths = EXCLUDED.strengths, "
                    "weaknesses = EXCLUDED.weaknesses, "
                    "notes = EXCLUDED.notes, "
                    "updated_at = NOW()"
                ),
                {
                    "email": student_email,
                    "ls": learning_style,
                    "dl": difficulty_level,
                    "strengths": strengths,
                    "weaknesses": weaknesses,
                    "notes": notes,
                },
            )
        return True
    except Exception as exc:
        logger.warning("upsert_student_profile_failed: %s", exc)
        return False


async def save_learning_memory(
    student_email: str,
    session_id: str,
    summary: str,
    topics_covered: str = "",
    mistakes_made: str = "",
    mastery_score: float = 0.0,
) -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO learning_memories "
                    "(student_email, session_id, summary, topics_covered, mistakes_made, mastery_score) "
                    "VALUES (:email, :session_id, :summary, :topics, :mistakes, :score)"
                ),
                {
                    "email": student_email,
                    "session_id": session_id,
                    "summary": summary,
                    "topics": topics_covered,
                    "mistakes": mistakes_made,
                    "score": mastery_score,
                },
            )
        return True
    except Exception as exc:
        logger.warning("save_learning_memory_failed: %s", exc)
        return False


async def get_recent_memories(student_email: str, limit: int = 5) -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT memory_id, student_email, session_id, summary, "
                    "topics_covered, mistakes_made, mastery_score, created_at "
                    "FROM learning_memories WHERE student_email = :email "
                    "ORDER BY created_at DESC LIMIT :limit"
                ),
                {"email": student_email, "limit": limit},
            )
            return [
                {
                    "memory_id": int(r[0]),
                    "student_email": str(r[1]),
                    "session_id": str(r[2]) if r[2] else "",
                    "summary": str(r[3]),
                    "topics_covered": str(r[4]),
                    "mistakes_made": str(r[5]),
                    "mastery_score": float(r[6]),
                    "created_at": r[7],
                }
                for r in result.fetchall()
            ]
    except Exception as exc:
        logger.warning("get_recent_memories_failed: %s", exc)
        return []


async def get_all_memories(student_email: str) -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT memory_id, student_email, session_id, summary, "
                    "topics_covered, mistakes_made, mastery_score, created_at "
                    "FROM learning_memories WHERE student_email = :email "
                    "ORDER BY created_at DESC"
                ),
                {"email": student_email},
            )
            return [
                {
                    "memory_id": int(r[0]),
                    "student_email": str(r[1]),
                    "session_id": str(r[2]) if r[2] else "",
                    "summary": str(r[3]),
                    "topics_covered": str(r[4]),
                    "mistakes_made": str(r[5]),
                    "mastery_score": float(r[6]),
                    "created_at": r[7],
                }
                for r in result.fetchall()
            ]
    except Exception as exc:
        logger.warning("get_all_memories_failed: %s", exc)
        return []


async def upsert_skill_assessment(
    student_email: str,
    topic: str,
    sub_skill: str,
    correct: bool,
) -> bool:
    try:
        async with engine.begin() as conn:
            correct_inc = 1 if correct else 0
            await conn.execute(
                text(
                    "INSERT INTO skill_assessments "
                    "(student_email, topic, sub_skill, correct_count, total_attempts, last_assessed_at) "
                    "VALUES (:email, :topic, :sub_skill, :correct_inc, 1, NOW()) "
                    "ON CONFLICT (student_email, topic, sub_skill) DO UPDATE SET "
                    "correct_count = skill_assessments.correct_count + :correct_inc, "
                    "total_attempts = skill_assessments.total_attempts + 1, "
                    "last_assessed_at = NOW()"
                ),
                {
                    "email": student_email,
                    "topic": topic,
                    "sub_skill": sub_skill,
                    "correct_inc": correct_inc,
                },
            )
        return True
    except Exception as exc:
        logger.warning("upsert_skill_assessment_failed: %s", exc)
        return False


async def get_skill_assessments(student_email: str) -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT id, student_email, topic, sub_skill, correct_count, "
                    "total_attempts, last_assessed_at "
                    "FROM skill_assessments WHERE student_email = :email "
                    "ORDER BY topic, sub_skill"
                ),
                {"email": student_email},
            )
            return [
                {
                    "id": int(r[0]),
                    "student_email": str(r[1]),
                    "topic": str(r[2]),
                    "sub_skill": str(r[3]),
                    "correct_count": int(r[4]),
                    "total_attempts": int(r[5]),
                    "last_assessed_at": r[6],
                }
                for r in result.fetchall()
            ]
    except Exception as exc:
        logger.warning("get_skill_assessments_failed: %s", exc)
        return []

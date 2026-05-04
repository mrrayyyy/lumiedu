from __future__ import annotations

import logging

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from auth import (
    ROLE_ADMIN,
    ROLE_PARENT,
    ROLE_STUDENT,
    ROLE_TEACHER,
    hash_password,
)
from config import settings

logger = logging.getLogger(__name__)

engine: AsyncEngine = create_async_engine(settings.database_url, echo=False, future=True)
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

_SCHEMA_SQL = [
    """
    CREATE TABLE IF NOT EXISTS auth_users (
        email TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'admin',
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """,
    """
    ALTER TABLE auth_users
        ADD COLUMN IF NOT EXISTS full_name TEXT NOT NULL DEFAULT '',
        ADD COLUMN IF NOT EXISTS grade_level TEXT,
        ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
    """,
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
    CREATE TABLE IF NOT EXISTS session_turns (
        turn_id BIGSERIAL PRIMARY KEY,
        session_id TEXT NOT NULL,
        transcript TEXT NOT NULL,
        assistant_response TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS classes (
        class_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        teacher_email TEXT NOT NULL REFERENCES auth_users(email) ON DELETE CASCADE,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS class_members (
        class_id TEXT NOT NULL REFERENCES classes(class_id) ON DELETE CASCADE,
        student_email TEXT NOT NULL REFERENCES auth_users(email) ON DELETE CASCADE,
        joined_at TIMESTAMP NOT NULL DEFAULT NOW(),
        PRIMARY KEY (class_id, student_email)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS lesson_assignments (
        assignment_id TEXT PRIMARY KEY,
        class_id TEXT NOT NULL REFERENCES classes(class_id) ON DELETE CASCADE,
        lesson_topic TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        due_at TIMESTAMP,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS parent_children (
        parent_email TEXT NOT NULL REFERENCES auth_users(email) ON DELETE CASCADE,
        child_email TEXT NOT NULL REFERENCES auth_users(email) ON DELETE CASCADE,
        PRIMARY KEY (parent_email, child_email)
    );
    """,
    # --- Phase 1: Knowledge Base ---
    """
    CREATE TABLE IF NOT EXISTS knowledge_documents (
        doc_id TEXT PRIMARY KEY,
        teacher_email TEXT NOT NULL REFERENCES auth_users(email) ON DELETE CASCADE,
        title TEXT NOT NULL,
        subject TEXT NOT NULL DEFAULT 'math',
        grade_level TEXT NOT NULL DEFAULT 'grade6',
        file_type TEXT NOT NULL DEFAULT 'txt',
        original_filename TEXT NOT NULL DEFAULT '',
        chunk_count INT NOT NULL DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS class_knowledge (
        class_id TEXT NOT NULL REFERENCES classes(class_id) ON DELETE CASCADE,
        doc_id TEXT NOT NULL REFERENCES knowledge_documents(doc_id) ON DELETE CASCADE,
        PRIMARY KEY (class_id, doc_id)
    );
    """,
    # --- Phase 2: Student Memory ---
    """
    CREATE TABLE IF NOT EXISTS student_profiles (
        student_email TEXT PRIMARY KEY REFERENCES auth_users(email) ON DELETE CASCADE,
        learning_style TEXT NOT NULL DEFAULT 'balanced',
        difficulty_level TEXT NOT NULL DEFAULT 'medium',
        preferred_language TEXT NOT NULL DEFAULT 'vi',
        strengths TEXT NOT NULL DEFAULT '[]',
        weaknesses TEXT NOT NULL DEFAULT '[]',
        notes TEXT NOT NULL DEFAULT '',
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS learning_memories (
        memory_id BIGSERIAL PRIMARY KEY,
        student_email TEXT NOT NULL REFERENCES auth_users(email) ON DELETE CASCADE,
        session_id TEXT REFERENCES learning_sessions(session_id) ON DELETE SET NULL,
        summary TEXT NOT NULL,
        topics_covered TEXT NOT NULL DEFAULT '',
        mistakes_made TEXT NOT NULL DEFAULT '',
        mastery_score FLOAT NOT NULL DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS skill_assessments (
        id BIGSERIAL PRIMARY KEY,
        student_email TEXT NOT NULL REFERENCES auth_users(email) ON DELETE CASCADE,
        topic TEXT NOT NULL,
        sub_skill TEXT NOT NULL,
        correct_count INT NOT NULL DEFAULT 0,
        total_attempts INT NOT NULL DEFAULT 0,
        last_assessed_at TIMESTAMP NOT NULL DEFAULT NOW(),
        UNIQUE (student_email, topic, sub_skill)
    );
    """,
    # --- Phase 3: Voice Cloning ---
    """
    CREATE TABLE IF NOT EXISTS teacher_voice_profiles (
        profile_id TEXT PRIMARY KEY,
        teacher_email TEXT NOT NULL REFERENCES auth_users(email) ON DELETE CASCADE,
        voice_name TEXT NOT NULL,
        provider TEXT NOT NULL DEFAULT 'gtts',
        model_path TEXT,
        external_voice_id TEXT,
        sample_count INT NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS class_voice_settings (
        class_id TEXT PRIMARY KEY REFERENCES classes(class_id) ON DELETE CASCADE,
        voice_profile_id TEXT NOT NULL REFERENCES teacher_voice_profiles(profile_id) ON DELETE CASCADE,
        enabled BOOLEAN NOT NULL DEFAULT TRUE
    );
    """,
]


_DEMO_USERS: list[tuple[str, str, str, str, str | None]] = [
    ("teacher@lumiedu.local", "Demo123!", ROLE_TEACHER, "Co giao Lan", None),
    ("student@lumiedu.local", "Demo123!", ROLE_STUDENT, "Hoc sinh Minh", "grade6"),
    ("parent@lumiedu.local", "Demo123!", ROLE_PARENT, "Phu huynh Hang", None),
]


async def ensure_db_ready() -> None:
    try:
        async with engine.begin() as conn:
            for sql in _SCHEMA_SQL:
                await conn.execute(text(sql))

            await conn.execute(
                text(
                    "INSERT INTO auth_users (email, password_hash, role, full_name) "
                    "VALUES (:email, :password_hash, :role, :full_name) "
                    "ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash, "
                    "role = EXCLUDED.role;"
                ),
                {
                    "email": settings.bootstrap_admin_email,
                    "password_hash": hash_password(settings.bootstrap_admin_password),
                    "role": ROLE_ADMIN,
                    "full_name": "Quan tri vien",
                },
            )

            for email, password, role, full_name, grade_level in _DEMO_USERS:
                await conn.execute(
                    text(
                        "INSERT INTO auth_users (email, password_hash, role, full_name, grade_level) "
                        "VALUES (:email, :password_hash, :role, :full_name, :grade_level) "
                        "ON CONFLICT (email) DO NOTHING;"
                    ),
                    {
                        "email": email,
                        "password_hash": hash_password(password),
                        "role": role,
                        "full_name": full_name,
                        "grade_level": grade_level,
                    },
                )

            await conn.execute(
                text(
                    "INSERT INTO parent_children (parent_email, child_email) "
                    "VALUES ('parent@lumiedu.local', 'student@lumiedu.local') "
                    "ON CONFLICT DO NOTHING;"
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
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "degraded"
    try:
        await redis_client.ping()
    except Exception:
        redis_status = "degraded"
    return {"postgres": db_status, "redis": redis_status}

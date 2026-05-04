from __future__ import annotations

import logging
from uuid import uuid4

from sqlalchemy import text

from core.database import engine

logger = logging.getLogger(__name__)


async def create_voice_profile(
    teacher_email: str,
    voice_name: str,
    provider: str = "gtts",
) -> str | None:
    profile_id = str(uuid4())
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO teacher_voice_profiles "
                    "(profile_id, teacher_email, voice_name, provider, status) "
                    "VALUES (:id, :email, :name, :provider, 'pending')"
                ),
                {
                    "id": profile_id,
                    "email": teacher_email,
                    "name": voice_name,
                    "provider": provider,
                },
            )
        return profile_id
    except Exception as exc:
        logger.warning("create_voice_profile_failed: %s", exc)
        return None


async def get_voice_profile(profile_id: str) -> dict[str, object] | None:
    try:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(
                        "SELECT profile_id, teacher_email, voice_name, provider, "
                        "model_path, external_voice_id, sample_count, status, created_at "
                        "FROM teacher_voice_profiles WHERE profile_id = :id"
                    ),
                    {"id": profile_id},
                )
            ).first()
            if not row:
                return None
            return {
                "profile_id": str(row[0]),
                "teacher_email": str(row[1]),
                "voice_name": str(row[2]),
                "provider": str(row[3]),
                "model_path": str(row[4]) if row[4] else None,
                "external_voice_id": str(row[5]) if row[5] else None,
                "sample_count": int(row[6]),
                "status": str(row[7]),
                "created_at": row[8],
            }
    except Exception as exc:
        logger.warning("get_voice_profile_failed: %s", exc)
        return None


async def list_voice_profiles_by_teacher(teacher_email: str) -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT profile_id, teacher_email, voice_name, provider, "
                    "model_path, external_voice_id, sample_count, status, created_at "
                    "FROM teacher_voice_profiles WHERE teacher_email = :email "
                    "ORDER BY created_at DESC"
                ),
                {"email": teacher_email},
            )
            return [
                {
                    "profile_id": str(r[0]),
                    "teacher_email": str(r[1]),
                    "voice_name": str(r[2]),
                    "provider": str(r[3]),
                    "model_path": str(r[4]) if r[4] else None,
                    "external_voice_id": str(r[5]) if r[5] else None,
                    "sample_count": int(r[6]),
                    "status": str(r[7]),
                    "created_at": r[8],
                }
                for r in result.fetchall()
            ]
    except Exception as exc:
        logger.warning("list_voice_profiles_by_teacher_failed: %s", exc)
        return []


async def update_voice_profile_status(
    profile_id: str,
    status: str,
    model_path: str | None = None,
    external_voice_id: str | None = None,
    sample_count: int | None = None,
) -> bool:
    try:
        async with engine.begin() as conn:
            updates = ["status = :status"]
            params: dict[str, object] = {"id": profile_id, "status": status}
            if model_path is not None:
                updates.append("model_path = :model_path")
                params["model_path"] = model_path
            if external_voice_id is not None:
                updates.append("external_voice_id = :ext_id")
                params["ext_id"] = external_voice_id
            if sample_count is not None:
                updates.append("sample_count = :sample_count")
                params["sample_count"] = sample_count

            set_clause = ", ".join(updates)
            await conn.execute(
                text(f"UPDATE teacher_voice_profiles SET {set_clause} WHERE profile_id = :id"),
                params,
            )
        return True
    except Exception as exc:
        logger.warning("update_voice_profile_status_failed: %s", exc)
        return False


async def delete_voice_profile(profile_id: str) -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM teacher_voice_profiles WHERE profile_id = :id"),
                {"id": profile_id},
            )
        return True
    except Exception as exc:
        logger.warning("delete_voice_profile_failed: %s", exc)
        return False


async def set_class_voice(class_id: str, voice_profile_id: str) -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO class_voice_settings (class_id, voice_profile_id, enabled) "
                    "VALUES (:class_id, :profile_id, TRUE) "
                    "ON CONFLICT (class_id) DO UPDATE SET "
                    "voice_profile_id = EXCLUDED.voice_profile_id, enabled = TRUE"
                ),
                {"class_id": class_id, "profile_id": voice_profile_id},
            )
        return True
    except Exception as exc:
        logger.warning("set_class_voice_failed: %s", exc)
        return False


async def get_class_voice(class_id: str) -> dict[str, object] | None:
    try:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(
                        "SELECT cvs.class_id, cvs.voice_profile_id, cvs.enabled, "
                        "tvp.voice_name, tvp.provider, tvp.status, tvp.external_voice_id "
                        "FROM class_voice_settings cvs "
                        "JOIN teacher_voice_profiles tvp ON tvp.profile_id = cvs.voice_profile_id "
                        "WHERE cvs.class_id = :class_id AND cvs.enabled = TRUE"
                    ),
                    {"class_id": class_id},
                )
            ).first()
            if not row:
                return None
            return {
                "class_id": str(row[0]),
                "voice_profile_id": str(row[1]),
                "enabled": bool(row[2]),
                "voice_name": str(row[3]),
                "provider": str(row[4]),
                "status": str(row[5]),
                "external_voice_id": str(row[6]) if row[6] else None,
            }
    except Exception as exc:
        logger.warning("get_class_voice_failed: %s", exc)
        return None


async def get_voice_for_learner(learner_email: str) -> dict[str, object] | None:
    try:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(
                        "SELECT DISTINCT cvs.voice_profile_id, tvp.voice_name, tvp.provider, "
                        "tvp.status, tvp.external_voice_id, tvp.model_path "
                        "FROM class_voice_settings cvs "
                        "JOIN teacher_voice_profiles tvp ON tvp.profile_id = cvs.voice_profile_id "
                        "JOIN class_members cm ON cm.class_id = cvs.class_id "
                        "WHERE cm.student_email = :email AND cvs.enabled = TRUE "
                        "AND tvp.status = 'ready' "
                        "LIMIT 1"
                    ),
                    {"email": learner_email},
                )
            ).first()
            if not row:
                return None
            return {
                "voice_profile_id": str(row[0]),
                "voice_name": str(row[1]),
                "provider": str(row[2]),
                "status": str(row[3]),
                "external_voice_id": str(row[4]) if row[4] else None,
                "model_path": str(row[5]) if row[5] else None,
            }
    except Exception as exc:
        logger.warning("get_voice_for_learner_failed: %s", exc)
        return None

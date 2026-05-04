from __future__ import annotations

import logging
from uuid import uuid4

from sqlalchemy import text

from core.database import engine

logger = logging.getLogger(__name__)


async def create_document(
    teacher_email: str,
    title: str,
    subject: str,
    grade_level: str,
    file_type: str,
    original_filename: str,
    chunk_count: int,
) -> str | None:
    doc_id = str(uuid4())
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO knowledge_documents "
                    "(doc_id, teacher_email, title, subject, grade_level, file_type, original_filename, chunk_count) "
                    "VALUES (:doc_id, :teacher_email, :title, :subject, :grade_level, :file_type, :original_filename, :chunk_count)"
                ),
                {
                    "doc_id": doc_id,
                    "teacher_email": teacher_email,
                    "title": title,
                    "subject": subject,
                    "grade_level": grade_level,
                    "file_type": file_type,
                    "original_filename": original_filename,
                    "chunk_count": chunk_count,
                },
            )
        return doc_id
    except Exception as exc:
        logger.warning("create_document_failed: %s", exc)
        return None


async def list_documents_by_teacher(teacher_email: str) -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT doc_id, teacher_email, title, subject, grade_level, "
                    "file_type, original_filename, chunk_count, created_at "
                    "FROM knowledge_documents WHERE teacher_email = :teacher_email "
                    "ORDER BY created_at DESC"
                ),
                {"teacher_email": teacher_email},
            )
            return [
                {
                    "doc_id": str(r[0]),
                    "teacher_email": str(r[1]),
                    "title": str(r[2]),
                    "subject": str(r[3]),
                    "grade_level": str(r[4]),
                    "file_type": str(r[5]),
                    "original_filename": str(r[6]),
                    "chunk_count": int(r[7]),
                    "created_at": r[8],
                }
                for r in result.fetchall()
            ]
    except Exception as exc:
        logger.warning("list_documents_by_teacher_failed: %s", exc)
        return []


async def list_all_documents() -> list[dict[str, object]]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT doc_id, teacher_email, title, subject, grade_level, "
                    "file_type, original_filename, chunk_count, created_at "
                    "FROM knowledge_documents ORDER BY created_at DESC"
                )
            )
            return [
                {
                    "doc_id": str(r[0]),
                    "teacher_email": str(r[1]),
                    "title": str(r[2]),
                    "subject": str(r[3]),
                    "grade_level": str(r[4]),
                    "file_type": str(r[5]),
                    "original_filename": str(r[6]),
                    "chunk_count": int(r[7]),
                    "created_at": r[8],
                }
                for r in result.fetchall()
            ]
    except Exception as exc:
        logger.warning("list_all_documents_failed: %s", exc)
        return []


async def get_document(doc_id: str) -> dict[str, object] | None:
    try:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(
                        "SELECT doc_id, teacher_email, title, subject, grade_level, "
                        "file_type, original_filename, chunk_count, created_at "
                        "FROM knowledge_documents WHERE doc_id = :doc_id"
                    ),
                    {"doc_id": doc_id},
                )
            ).first()
            if not row:
                return None
            return {
                "doc_id": str(row[0]),
                "teacher_email": str(row[1]),
                "title": str(row[2]),
                "subject": str(row[3]),
                "grade_level": str(row[4]),
                "file_type": str(row[5]),
                "original_filename": str(row[6]),
                "chunk_count": int(row[7]),
                "created_at": row[8],
            }
    except Exception as exc:
        logger.warning("get_document_failed: %s", exc)
        return None


async def delete_document(doc_id: str) -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM knowledge_documents WHERE doc_id = :doc_id"),
                {"doc_id": doc_id},
            )
        return True
    except Exception as exc:
        logger.warning("delete_document_failed: %s", exc)
        return False


async def link_document_to_class(class_id: str, doc_id: str) -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO class_knowledge (class_id, doc_id) "
                    "VALUES (:class_id, :doc_id) ON CONFLICT DO NOTHING"
                ),
                {"class_id": class_id, "doc_id": doc_id},
            )
        return True
    except Exception as exc:
        logger.warning("link_document_to_class_failed: %s", exc)
        return False


async def unlink_document_from_class(class_id: str, doc_id: str) -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "DELETE FROM class_knowledge "
                    "WHERE class_id = :class_id AND doc_id = :doc_id"
                ),
                {"class_id": class_id, "doc_id": doc_id},
            )
        return True
    except Exception as exc:
        logger.warning("unlink_document_from_class_failed: %s", exc)
        return False


async def get_class_doc_ids(class_id: str) -> list[str]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT doc_id FROM class_knowledge WHERE class_id = :class_id"),
                {"class_id": class_id},
            )
            return [str(r[0]) for r in result.fetchall()]
    except Exception as exc:
        logger.warning("get_class_doc_ids_failed: %s", exc)
        return []


async def get_doc_ids_for_learner(learner_email: str) -> list[str]:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT DISTINCT ck.doc_id FROM class_knowledge ck "
                    "JOIN class_members cm ON cm.class_id = ck.class_id "
                    "WHERE cm.student_email = :student_email"
                ),
                {"student_email": learner_email},
            )
            return [str(r[0]) for r in result.fetchall()]
    except Exception as exc:
        logger.warning("get_doc_ids_for_learner_failed: %s", exc)
        return []

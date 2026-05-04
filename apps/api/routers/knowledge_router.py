from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from auth import (
    CurrentUser,
    ROLE_ADMIN,
    ROLE_TEACHER,
    get_current_user,
    require_roles,
)
from config import settings
from repos.knowledge_repo import (
    create_document,
    delete_document,
    get_class_doc_ids,
    get_document,
    link_document_to_class,
    list_all_documents,
    list_documents_by_teacher,
    unlink_document_from_class,
    update_document_chunk_count,
)
from repos.class_repo import get_class
from schemas import (
    ClassKnowledgeLinkRequest,
    KnowledgeDocumentResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])

KNOWLEDGE_SERVICE_URL = getattr(settings, "knowledge_url", "http://knowledge-service:8104")


def _doc_to_response(d: dict[str, object]) -> KnowledgeDocumentResponse:
    return KnowledgeDocumentResponse(
        doc_id=str(d["doc_id"]),
        teacher_email=str(d["teacher_email"]),
        title=str(d["title"]),
        subject=str(d["subject"]),
        grade_level=str(d["grade_level"]),
        file_type=str(d["file_type"]),
        original_filename=str(d["original_filename"]),
        chunk_count=int(d["chunk_count"]),
        created_at=d["created_at"],  # type: ignore[arg-type]
    )


@router.post("/upload", response_model=KnowledgeDocumentResponse, status_code=201)
async def upload_knowledge(
    file: UploadFile = File(...),
    title: str = Form(...),
    subject: str = Form(default="math"),
    grade_level: str = Form(default="grade6"),
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> KnowledgeDocumentResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in ("pdf", "docx", "txt", "md"):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    content = await file.read()
    max_bytes = 20 * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail="File too large (max 20MB)")

    doc_id = await create_document(
        teacher_email=current.email,
        title=title,
        subject=subject,
        grade_level=grade_level,
        file_type=suffix,
        original_filename=file.filename,
        chunk_count=0,
    )
    if not doc_id:
        raise HTTPException(status_code=500, detail="Failed to create document record")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{KNOWLEDGE_SERVICE_URL}/upload",
                files={"file": (file.filename, content, file.content_type or "application/octet-stream")},
                data={"doc_id": doc_id, "teacher_email": current.email},
            )
            response.raise_for_status()
            result = response.json()
            chunk_count = int(result.get("chunk_count", 0))
    except Exception as exc:
        await delete_document(doc_id)
        logger.warning("knowledge_service_upload_failed: %s", exc)
        raise HTTPException(status_code=502, detail="Knowledge service upload failed") from exc

    await update_document_chunk_count(doc_id, chunk_count)

    doc = await get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=500, detail="Failed to fetch document")
    doc["chunk_count"] = chunk_count
    return _doc_to_response(doc)


@router.get("", response_model=list[KnowledgeDocumentResponse])
async def list_knowledge(
    current: CurrentUser = Depends(get_current_user),
) -> list[KnowledgeDocumentResponse]:
    if current.role == ROLE_ADMIN:
        docs = await list_all_documents()
    elif current.role == ROLE_TEACHER:
        docs = await list_documents_by_teacher(current.email)
    else:
        raise HTTPException(status_code=403, detail="Only teachers and admins can list documents")
    return [_doc_to_response(d) for d in docs]


@router.delete("/{doc_id}")
async def delete_knowledge(
    doc_id: str,
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> dict[str, str]:
    doc = await get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if current.role == ROLE_TEACHER and doc["teacher_email"] != current.email:
        raise HTTPException(status_code=403, detail="Not your document")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.delete(f"{KNOWLEDGE_SERVICE_URL}/documents/{doc_id}")
    except Exception as exc:
        logger.warning("knowledge_service_delete_failed: %s", exc)

    await delete_document(doc_id)
    return {"status": "deleted", "doc_id": doc_id}


@router.post("/classes/{class_id}/link")
async def link_knowledge_to_class(
    class_id: str,
    payload: ClassKnowledgeLinkRequest,
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> dict[str, str]:
    klass = await get_class(class_id)
    if not klass:
        raise HTTPException(status_code=404, detail="Class not found")
    if current.role == ROLE_TEACHER and klass["teacher_email"] != current.email:
        raise HTTPException(status_code=403, detail="Not your class")

    doc = await get_document(payload.doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    success = await link_document_to_class(class_id, payload.doc_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to link document")
    return {"status": "linked", "class_id": class_id, "doc_id": payload.doc_id}


@router.delete("/classes/{class_id}/link/{doc_id}")
async def unlink_knowledge_from_class(
    class_id: str,
    doc_id: str,
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> dict[str, str]:
    klass = await get_class(class_id)
    if not klass:
        raise HTTPException(status_code=404, detail="Class not found")
    if current.role == ROLE_TEACHER and klass["teacher_email"] != current.email:
        raise HTTPException(status_code=403, detail="Not your class")

    await unlink_document_from_class(class_id, doc_id)
    return {"status": "unlinked", "class_id": class_id, "doc_id": doc_id}


@router.get("/classes/{class_id}/docs", response_model=list[KnowledgeDocumentResponse])
async def list_class_knowledge(
    class_id: str,
    current: CurrentUser = Depends(get_current_user),
) -> list[KnowledgeDocumentResponse]:
    klass = await get_class(class_id)
    if not klass:
        raise HTTPException(status_code=404, detail="Class not found")

    doc_ids = await get_class_doc_ids(class_id)
    docs = []
    for did in doc_ids:
        doc = await get_document(did)
        if doc:
            docs.append(_doc_to_response(doc))
    return docs

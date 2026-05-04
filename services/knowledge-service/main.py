from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, UploadFile, File, Form, HTTPException

from config import settings
from providers import TextChunker, VectorStoreProvider
from schemas import (
    DocumentUploadResponse,
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    RetrievedChunk,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("knowledge-service")

app = FastAPI(title="LumiEdu Knowledge Service")

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "knowledge"}


@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    doc_id: str = Form(default=""),
    teacher_email: str = Form(default=""),
) -> DocumentUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max: {settings.max_file_size_mb}MB",
        )

    assigned_id = doc_id or str(uuid4())

    text = TextChunker.extract_text(content, file.filename)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    chunks = TextChunker.chunk_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="No text chunks extracted")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{assigned_id}{suffix}"
    file_path.write_bytes(content)

    chunk_count = VectorStoreProvider.index_chunks(assigned_id, file.filename, chunks)

    logger.info(
        "document_uploaded doc_id=%s filename=%s chunks=%d teacher=%s",
        assigned_id, file.filename, chunk_count, teacher_email,
    )

    return DocumentUploadResponse(
        doc_id=assigned_id,
        filename=file.filename,
        chunk_count=chunk_count,
    )


@app.post("/query", response_model=KnowledgeQueryResponse)
async def query_knowledge(payload: KnowledgeQueryRequest) -> KnowledgeQueryResponse:
    raw_chunks = VectorStoreProvider.query(
        query=payload.query,
        doc_ids=payload.doc_ids if payload.doc_ids else None,
        top_k=payload.top_k,
    )

    chunks = [
        RetrievedChunk(
            text=str(c["text"]),
            doc_id=str(c["doc_id"]),
            filename=str(c["filename"]),
            chunk_index=int(c["chunk_index"]),
            score=float(c["score"]),
        )
        for c in raw_chunks
    ]

    return KnowledgeQueryResponse(query=payload.query, chunks=chunks)


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str) -> dict[str, str]:
    success = VectorStoreProvider.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or delete failed")

    file_dir = Path(settings.upload_dir)
    for f in file_dir.glob(f"{doc_id}.*"):
        f.unlink(missing_ok=True)

    return {"status": "deleted", "doc_id": doc_id}

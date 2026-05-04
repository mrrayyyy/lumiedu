from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    doc_id: str
    filename: str
    chunk_count: int
    status: str = "indexed"


class KnowledgeQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    doc_ids: list[str] = Field(default_factory=list, description="Filter by specific document IDs")
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievedChunk(BaseModel):
    text: str
    doc_id: str
    filename: str
    chunk_index: int
    score: float


class KnowledgeQueryResponse(BaseModel):
    query: str
    chunks: list[RetrievedChunk]

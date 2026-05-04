from __future__ import annotations

import logging
from pathlib import Path

import chromadb

from config import settings
from providers.embeddings import EmbeddingProvider

logger = logging.getLogger("knowledge.vectorstore")

_client: chromadb.ClientAPI | None = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        persist_dir = Path(settings.chromadb_persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(persist_dir))
        logger.info("ChromaDB initialized at %s", persist_dir)
    return _client


COLLECTION_NAME = "knowledge_chunks"


class VectorStoreProvider:
    @staticmethod
    def index_chunks(
        doc_id: str,
        filename: str,
        chunks: list[str],
    ) -> int:
        client = _get_client()
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        embeddings = EmbeddingProvider.embed_texts(chunks)

        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {"doc_id": doc_id, "filename": filename, "chunk_index": i}
            for i in range(len(chunks))
        ]

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )

        logger.info("Indexed %d chunks for doc %s", len(chunks), doc_id)
        return len(chunks)

    @staticmethod
    def query(
        query: str,
        doc_ids: list[str] | None = None,
        top_k: int = 5,
    ) -> list[dict[str, object]]:
        client = _get_client()
        try:
            collection = client.get_collection(name=COLLECTION_NAME)
        except Exception:
            return []

        query_embedding = EmbeddingProvider.embed_query(query)

        where_filter = None
        if doc_ids:
            if len(doc_ids) == 1:
                where_filter = {"doc_id": doc_ids[0]}
            else:
                where_filter = {"doc_id": {"$in": doc_ids}}

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        chunks: list[dict[str, object]] = []
        if results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
            distances = results["distances"][0] if results["distances"] else [0.0] * len(docs)

            for doc_text, meta, dist in zip(docs, metas, distances):
                score = 1.0 - float(dist)
                chunks.append({
                    "text": str(doc_text),
                    "doc_id": str(meta.get("doc_id", "")),
                    "filename": str(meta.get("filename", "")),
                    "chunk_index": int(meta.get("chunk_index", 0)),
                    "score": round(score, 4),
                })

        return chunks

    @staticmethod
    def delete_document(doc_id: str) -> bool:
        client = _get_client()
        try:
            collection = client.get_collection(name=COLLECTION_NAME)
            collection.delete(where={"doc_id": doc_id})
            logger.info("Deleted chunks for doc %s", doc_id)
            return True
        except Exception as exc:
            logger.warning("Delete failed for doc %s: %s", doc_id, exc)
            return False

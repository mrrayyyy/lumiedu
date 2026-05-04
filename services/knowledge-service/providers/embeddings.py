from __future__ import annotations

import logging

from config import settings

logger = logging.getLogger("knowledge.embeddings")

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model: %s", settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded")
    return _model


class EmbeddingProvider:
    @staticmethod
    def embed_texts(texts: list[str]) -> list[list[float]]:
        model = _get_model()
        embeddings = model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    @staticmethod
    def embed_query(query: str) -> list[float]:
        model = _get_model()
        embedding = model.encode([query], show_progress_bar=False)
        return embedding[0].tolist()

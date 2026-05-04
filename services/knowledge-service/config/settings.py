import os


class Settings:
    chromadb_persist_dir: str = os.getenv("CHROMADB_PERSIST_DIR", "/app/chromadb_data")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    upload_dir: str = os.getenv("UPLOAD_DIR", "/app/uploads")
    max_chunk_size: int = int(os.getenv("MAX_CHUNK_SIZE", "800"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
    top_k_results: int = int(os.getenv("TOP_K_RESULTS", "5"))


settings = Settings()

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    chromadb_persist_dir: str = Field(default="/app/chromadb_data", validation_alias="CHROMADB_PERSIST_DIR")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", validation_alias="EMBEDDING_MODEL")
    upload_dir: str = Field(default="/app/uploads", validation_alias="UPLOAD_DIR")
    max_chunk_size: int = Field(default=800, validation_alias="MAX_CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, validation_alias="CHUNK_OVERLAP")
    max_file_size_mb: int = Field(default=20, validation_alias="MAX_FILE_SIZE_MB")
    top_k_results: int = Field(default=5, validation_alias="TOP_K_RESULTS")


settings = Settings()

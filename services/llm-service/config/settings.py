from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ollama_base_url: str = Field(default="", validation_alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.2:3b", validation_alias="OLLAMA_MODEL")
    ollama_timeout: float = Field(default=30.0, validation_alias="OLLAMA_TIMEOUT")
    max_history_turns: int = Field(default=10, validation_alias="MAX_HISTORY_TURNS")
    max_response_tokens: int = Field(default=256, validation_alias="MAX_RESPONSE_TOKENS")
    temperature: float = Field(default=0.7, validation_alias="LLM_TEMPERATURE")


settings = Settings()

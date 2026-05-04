from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    model_size: str = Field(default="base", validation_alias="WHISPER_MODEL_SIZE")
    device: str = Field(default="cpu", validation_alias="WHISPER_DEVICE")
    compute_type: str = Field(default="int8", validation_alias="WHISPER_COMPUTE_TYPE")
    external_provider_url: str = Field(default="", validation_alias="STT_PROVIDER_URL")
    beam_size: int = Field(default=5, validation_alias="WHISPER_BEAM_SIZE")
    vad_enabled: bool = Field(default=True, validation_alias="WHISPER_VAD_ENABLED")
    vad_min_silence_ms: int = Field(default=300, validation_alias="WHISPER_VAD_MIN_SILENCE_MS")
    default_language: str = Field(default="vi", validation_alias="STT_DEFAULT_LANGUAGE")


settings = Settings()

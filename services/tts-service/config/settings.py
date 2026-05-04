from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    external_provider_url: str = Field(default="", validation_alias="TTS_PROVIDER_URL")
    audio_cache_dir: str = Field(default="/app/audio_cache", validation_alias="TTS_AUDIO_CACHE_DIR")
    max_cache_files: int = Field(default=500, validation_alias="TTS_MAX_CACHE_FILES")
    default_voice: str = Field(default="warm_teacher", validation_alias="TTS_DEFAULT_VOICE")
    gtts_enabled: bool = Field(default=True, validation_alias="TTS_GTTS_ENABLED")
    gtts_language: str = Field(default="vi", validation_alias="TTS_GTTS_LANGUAGE")
    gtts_slow: bool = Field(default=True, validation_alias="TTS_GTTS_SLOW")


settings = Settings()

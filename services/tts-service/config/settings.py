import os


class Settings:
    external_provider_url: str = os.getenv("TTS_PROVIDER_URL", "").strip()
    audio_cache_dir: str = os.getenv("TTS_AUDIO_CACHE_DIR", "/app/audio_cache")
    max_cache_files: int = int(os.getenv("TTS_MAX_CACHE_FILES", "500"))
    default_voice: str = os.getenv("TTS_DEFAULT_VOICE", "warm_teacher")
    gtts_enabled: bool = os.getenv("TTS_GTTS_ENABLED", "true").lower() == "true"
    gtts_language: str = os.getenv("TTS_GTTS_LANGUAGE", "vi")
    gtts_slow: bool = os.getenv("TTS_GTTS_SLOW", "true").lower() == "true"


settings = Settings()

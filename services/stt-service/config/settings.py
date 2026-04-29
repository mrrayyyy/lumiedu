import os


class Settings:
    model_size: str = os.getenv("WHISPER_MODEL_SIZE", "base")
    device: str = os.getenv("WHISPER_DEVICE", "cpu")
    compute_type: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    external_provider_url: str = os.getenv("STT_PROVIDER_URL", "").strip()
    beam_size: int = int(os.getenv("WHISPER_BEAM_SIZE", "5"))
    vad_enabled: bool = os.getenv("WHISPER_VAD_ENABLED", "true").lower() == "true"
    vad_min_silence_ms: int = int(os.getenv("WHISPER_VAD_MIN_SILENCE_MS", "300"))
    default_language: str = os.getenv("STT_DEFAULT_LANGUAGE", "vi")


settings = Settings()

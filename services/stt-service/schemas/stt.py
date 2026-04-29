from pydantic import BaseModel, Field


class STTRequest(BaseModel):
    text_hint: str | None = Field(default=None, description="Text input fallback for MVP")
    audio_base64: str | None = Field(default=None, description="Base64 encoded audio (WAV/WebM)")
    language: str = "vi"


class STTResponse(BaseModel):
    transcript: str
    language: str
    duration_ms: int = 0
    provider: str = "mock"

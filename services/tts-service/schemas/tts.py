from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    text: str = Field(default="")
    voice: str = "warm_teacher"
    language: str = "vi"


class TTSResponse(BaseModel):
    audio_url: str
    text: str
    duration_ms: int = 0
    provider: str = "mock"

import os

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="LumiEdu STT Service")


class STTRequest(BaseModel):
    text_hint: str | None = Field(default=None, description="Temporary text input for MVP")
    audio_base64: str | None = Field(default=None, description="Base64 encoded audio for real STT providers")
    language: str = "vi"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "stt"}


@app.post("/transcribe")
async def transcribe(payload: STTRequest) -> dict[str, str]:
    provider_url = os.getenv("STT_PROVIDER_URL", "").strip()
    if provider_url and payload.audio_base64:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                provider_url,
                json={"audio_base64": payload.audio_base64, "language": payload.language},
            )
            response.raise_for_status()
            transcript = str(response.json().get("transcript", "")).strip()
            if transcript:
                return {"transcript": transcript, "language": payload.language}

    transcript = payload.text_hint or ""
    return {"transcript": transcript.strip(), "language": payload.language}

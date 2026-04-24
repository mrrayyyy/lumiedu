import os

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="LumiEdu TTS Service")


class TTSRequest(BaseModel):
    text: str = Field(default="")
    voice: str = "warm_teacher"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "tts"}


@app.post("/synthesize")
async def synthesize(payload: TTSRequest) -> dict[str, str]:
    provider_url = os.getenv("TTS_PROVIDER_URL", "").strip()
    if provider_url and payload.text.strip():
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                provider_url,
                json={"text": payload.text, "voice": payload.voice},
            )
            response.raise_for_status()
            audio_url = str(response.json().get("audio_url", "")).strip()
            if audio_url:
                return {"audio_url": audio_url, "text": payload.text}

    return {
        "audio_url": f"/audio/mock/{payload.voice}",
        "text": payload.text,
    }

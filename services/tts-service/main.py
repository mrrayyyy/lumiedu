from __future__ import annotations

import logging
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from providers import ExternalProvider, GTTSProvider
from schemas import TTSRequest, TTSResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="LumiEdu TTS Service")

cache_dir = Path(settings.audio_cache_dir)
cache_dir.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(cache_dir)), name="audio")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "tts",
        "gtts_available": "yes" if GTTSProvider.is_available() else "no",
        "external_configured": "yes" if ExternalProvider.is_available() else "no",
    }


@app.post("/synthesize", response_model=TTSResponse)
async def synthesize(payload: TTSRequest) -> TTSResponse:
    started = time.perf_counter()
    text = payload.text.strip()

    if not text:
        return _response("", text, started, "mock")

    if ExternalProvider.is_available():
        result = await ExternalProvider.synthesize(text, payload.voice)
        if result:
            return _response(result, text, started, "external")

    if GTTSProvider.is_available():
        result = GTTSProvider.synthesize(text, payload.language)
        if result:
            return _response(result, text, started, "gtts")

    return _response(f"/audio/mock/{payload.voice}", text, started, "mock")


def _response(audio_url: str, text: str, started: float, provider: str) -> TTSResponse:
    elapsed = int((time.perf_counter() - started) * 1000)
    return TTSResponse(
        audio_url=audio_url,
        text=text,
        duration_ms=elapsed,
        provider=provider,
    )

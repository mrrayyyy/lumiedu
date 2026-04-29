from __future__ import annotations

import base64
import logging
import time

from fastapi import FastAPI, File, Form, UploadFile

from config import settings
from providers import ExternalProvider, WhisperProvider
from schemas import STTRequest, STTResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="LumiEdu STT Service")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "stt",
        "whisper_available": "yes" if WhisperProvider.is_available() else "no",
        "model_size": settings.model_size,
    }


@app.post("/transcribe", response_model=STTResponse)
async def transcribe(payload: STTRequest) -> STTResponse:
    started = time.perf_counter()

    if payload.audio_base64:
        audio_bytes = _decode_base64(payload.audio_base64)

        if audio_bytes:
            result = WhisperProvider.transcribe(audio_bytes, payload.language)
            if result:
                return _response(result, payload.language, started, "faster-whisper")

            result = await ExternalProvider.transcribe(payload.audio_base64, payload.language)
            if result:
                return _response(result, payload.language, started, "external")

    transcript = (payload.text_hint or "").strip()
    provider = "text_hint" if payload.text_hint else "mock"
    return _response(transcript, payload.language, started, provider)


@app.post("/transcribe/upload", response_model=STTResponse)
async def transcribe_upload(
    audio: UploadFile = File(...),
    language: str = Form("vi"),
) -> STTResponse:
    started = time.perf_counter()
    audio_bytes = await audio.read()

    if audio_bytes:
        result = WhisperProvider.transcribe(audio_bytes, language)
        if result:
            return _response(result, language, started, "faster-whisper")

    return _response("", language, started, "mock")


def _decode_base64(data: str) -> bytes:
    try:
        return base64.b64decode(data)
    except Exception:
        return b""


def _response(transcript: str, language: str, started: float, provider: str) -> STTResponse:
    elapsed = int((time.perf_counter() - started) * 1000)
    return STTResponse(
        transcript=transcript,
        language=language,
        duration_ms=elapsed,
        provider=provider,
    )

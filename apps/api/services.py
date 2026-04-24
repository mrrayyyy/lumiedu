from __future__ import annotations

import time
import httpx

from config import settings


class VoiceOrchestrator:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)

    async def close(self) -> None:
        await self._client.aclose()

    async def run_turn(self, text_input: str) -> dict[str, str | int]:
        started_at = time.perf_counter()

        stt_response = await self._client.post(
            f"{settings.stt_url}/transcribe",
            json={"text_hint": text_input, "language": "vi"},
        )
        stt_response.raise_for_status()
        transcript = stt_response.json().get("transcript", "")

        llm_response = await self._client.post(
            f"{settings.llm_url}/respond",
            json={"transcript": transcript, "learner_level": "grade6"},
        )
        llm_response.raise_for_status()
        assistant_response = llm_response.json().get("assistant_response", "")

        tts_response = await self._client.post(
            f"{settings.tts_url}/synthesize",
            json={"text": assistant_response, "voice": "warm_teacher"},
        )
        tts_response.raise_for_status()
        audio_url = tts_response.json().get("audio_url", "")

        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        return {
            "transcript": transcript,
            "assistant_response": assistant_response,
            "audio_url": audio_url,
            "response_ms": elapsed_ms,
        }

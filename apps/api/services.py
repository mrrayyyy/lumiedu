from __future__ import annotations

import logging
import time

import httpx

from config import settings

logger = logging.getLogger("lumiedu.orchestrator")

_MAX_RETRIES = 2
_RETRY_DELAY = 0.5


class VoiceOrchestrator:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)

    async def close(self) -> None:
        await self._client.aclose()

    async def run_turn(
        self,
        text_input: str,
        audio_base64: str | None = None,
        lesson_topic: str = "",
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, str | int]:
        started_at = time.perf_counter()

        transcript = await self._stt(text_input, audio_base64)
        assistant_response = await self._llm(transcript, lesson_topic, history or [])
        audio_url = await self._tts(assistant_response)

        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        return {
            "transcript": transcript,
            "assistant_response": assistant_response,
            "audio_url": audio_url,
            "response_ms": elapsed_ms,
        }

    async def _stt(self, text_input: str, audio_base64: str | None) -> str:
        payload: dict[str, str | None] = {"language": "vi"}
        if audio_base64:
            payload["audio_base64"] = audio_base64
        else:
            payload["text_hint"] = text_input

        data = await self._request_with_retry(
            f"{settings.stt_url}/transcribe",
            payload,
        )
        return str(data.get("transcript", text_input))

    async def _llm(
        self,
        transcript: str,
        lesson_topic: str,
        history: list[dict[str, str]],
    ) -> str:
        payload: dict[str, object] = {
            "transcript": transcript,
            "learner_level": "grade6",
            "lesson_topic": lesson_topic,
            "history": history,
        }
        data = await self._request_with_retry(
            f"{settings.llm_url}/respond",
            payload,
        )
        return str(data.get("assistant_response", ""))

    async def _tts(self, text: str) -> str:
        payload = {"text": text, "voice": "warm_teacher", "language": "vi"}
        data = await self._request_with_retry(
            f"{settings.tts_url}/synthesize",
            payload,
        )
        return str(data.get("audio_url", ""))

    async def _request_with_retry(
        self,
        url: str,
        payload: dict[str, object],
    ) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                response = await self._client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "request_failed attempt=%d url=%s error=%s",
                    attempt + 1,
                    url,
                    exc,
                )
                if attempt < _MAX_RETRIES:
                    import asyncio

                    await asyncio.sleep(_RETRY_DELAY * (attempt + 1))

        raise last_error or RuntimeError(f"Request to {url} failed")

from __future__ import annotations

import logging

import httpx

from config import settings

logger = logging.getLogger("stt.external")


class ExternalProvider:
    @staticmethod
    def is_available() -> bool:
        return bool(settings.external_provider_url)

    @staticmethod
    async def transcribe(audio_base64: str, language: str) -> str | None:
        if not settings.external_provider_url:
            return None

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    settings.external_provider_url,
                    json={"audio_base64": audio_base64, "language": language},
                )
                response.raise_for_status()
                text = str(response.json().get("transcript", "")).strip()
                return text if text else None
        except Exception as exc:
            logger.warning("external transcribe failed: %s", exc)
            return None

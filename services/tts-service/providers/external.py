from __future__ import annotations

import logging

import httpx

from config import settings

logger = logging.getLogger("tts.external")


class ExternalProvider:
    @staticmethod
    def is_available() -> bool:
        return bool(settings.external_provider_url)

    @staticmethod
    async def synthesize(text: str, voice: str) -> str | None:
        if not settings.external_provider_url:
            return None

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    settings.external_provider_url,
                    json={"text": text, "voice": voice},
                )
                response.raise_for_status()
                audio_url = str(response.json().get("audio_url", "")).strip()
                return audio_url if audio_url else None
        except Exception as exc:
            logger.warning("external synthesis failed: %s", exc)
            return None

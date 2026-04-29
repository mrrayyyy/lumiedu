from __future__ import annotations

import logging

import httpx

from config import settings, SOCRATIC_SYSTEM_PROMPT
from config.prompts import TOPIC_PROMPTS, detect_topic
from schemas import HistoryItem

logger = logging.getLogger("llm.ollama")


class OllamaProvider:
    @staticmethod
    def is_available() -> bool:
        return bool(settings.ollama_base_url)

    @staticmethod
    def _build_prompt(
        transcript: str,
        lesson_topic: str,
        history: list[HistoryItem],
    ) -> str:
        parts = [SOCRATIC_SYSTEM_PROMPT, ""]

        topic_key = detect_topic(transcript) or detect_topic(lesson_topic)
        if topic_key and topic_key in TOPIC_PROMPTS:
            parts.append(TOPIC_PROMPTS[topic_key])
            parts.append("")

        if history:
            recent = history[-settings.max_history_turns :]
            parts.append("LICH SU HOI THOAI GAN DAY:")
            for item in recent:
                speaker = "Hoc sinh" if item.role == "learner" else "Gia su"
                parts.append(f"- {speaker}: {item.text}")
            parts.append("")

        parts.append(f"Hoc sinh noi: {transcript}")
        return "\n".join(parts)

    @staticmethod
    async def respond(
        transcript: str,
        lesson_topic: str,
        history: list[HistoryItem],
    ) -> str | None:
        if not settings.ollama_base_url:
            return None

        prompt = OllamaProvider._build_prompt(transcript, lesson_topic, history)

        try:
            async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
                response = await client.post(
                    f"{settings.ollama_base_url.rstrip('/')}/api/generate",
                    json={
                        "model": settings.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": settings.temperature,
                            "num_predict": settings.max_response_tokens,
                        },
                    },
                )
                response.raise_for_status()
                text = str(response.json().get("response", "")).strip()
                return text if text else None
        except Exception as exc:
            logger.warning("ollama request failed: %s", exc)
            return None

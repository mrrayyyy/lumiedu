from __future__ import annotations

import logging

import httpx

from config import settings, SOCRATIC_SYSTEM_PROMPT
from config.prompts import TOPIC_PROMPTS, detect_topic
from schemas import HistoryItem, StudentContext

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
        context_chunks: list[str] | None = None,
        student_context: StudentContext | None = None,
    ) -> str:
        parts = [SOCRATIC_SYSTEM_PROMPT, ""]

        topic_key = detect_topic(transcript) or detect_topic(lesson_topic)
        if topic_key and topic_key in TOPIC_PROMPTS:
            parts.append(TOPIC_PROMPTS[topic_key])
            parts.append("")

        if student_context:
            parts.append("THONG TIN HOC SINH:")
            parts.append(f"- Phong cach hoc: {student_context.learning_style}")
            parts.append(f"- Muc do kho: {student_context.difficulty_level}")
            if student_context.strengths and student_context.strengths != "[]":
                parts.append(f"- Diem manh: {student_context.strengths}")
            if student_context.weaknesses and student_context.weaknesses != "[]":
                parts.append(f"- Diem yeu: {student_context.weaknesses}")
            if student_context.recent_summaries:
                parts.append("- Tom tat buoi hoc gan day:")
                for summary in student_context.recent_summaries[-3:]:
                    parts.append(f"  + {summary}")
            parts.append("")

        if context_chunks:
            parts.append("TAI LIEU THAM KHAO (su dung de tra loi chinh xac hon):")
            for i, chunk in enumerate(context_chunks[:5], 1):
                parts.append(f"[{i}] {chunk}")
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
        context_chunks: list[str] | None = None,
        student_context: StudentContext | None = None,
    ) -> str | None:
        if not settings.ollama_base_url:
            return None

        prompt = OllamaProvider._build_prompt(
            transcript, lesson_topic, history, context_chunks, student_context,
        )

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

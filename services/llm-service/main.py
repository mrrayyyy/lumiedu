from __future__ import annotations

import logging

from fastapi import FastAPI

from config import settings
from config.prompts import detect_topic
from providers import MockProvider, OllamaProvider
from schemas import LLMRequest, LLMResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="LumiEdu LLM Service")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "llm",
        "ollama_configured": "yes" if OllamaProvider.is_available() else "no",
        "model": settings.ollama_model,
    }


@app.post("/respond", response_model=LLMResponse)
async def respond(payload: LLMRequest) -> LLMResponse:
    transcript = payload.transcript.strip()
    topic = detect_topic(transcript) or detect_topic(payload.lesson_topic) or ""

    if not transcript:
        return LLMResponse(
            assistant_response=MockProvider.respond(""),
            topic_detected=topic,
            provider="mock",
        )

    if OllamaProvider.is_available():
        result = await OllamaProvider.respond(
            transcript=transcript,
            lesson_topic=payload.lesson_topic,
            history=payload.history,
        )
        if result:
            return LLMResponse(
                assistant_response=result,
                topic_detected=topic,
                provider="ollama",
            )

    return LLMResponse(
        assistant_response=MockProvider.respond(transcript),
        topic_detected=topic,
        provider="mock",
    )

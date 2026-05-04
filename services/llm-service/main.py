from __future__ import annotations

import logging

from fastapi import FastAPI

from config import settings
from config.prompts import detect_topic
from providers import MockProvider, OllamaProvider
from schemas import LLMRequest, LLMResponse, SummarizeRequest, SummarizeResponse

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
            context_chunks=payload.context_chunks or None,
            student_context=payload.student_context,
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


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_session(payload: SummarizeRequest) -> SummarizeResponse:
    if not payload.session_turns:
        return SummarizeResponse(summary="Khong co noi dung de tom tat.")

    conversation = []
    for turn in payload.session_turns:
        speaker = "Hoc sinh" if turn.role == "learner" else "Gia su"
        conversation.append(f"{speaker}: {turn.text}")
    convo_text = "\n".join(conversation)

    summary_prompt = (
        "Tom tat ngan gon buoi hoc sau day (toi da 3 cau). "
        "Ghi lai: chu de da hoc, diem hoc sinh lam tot, diem can cai thien.\n\n"
        f"Chu de: {payload.lesson_topic}\n\n"
        f"Hoi thoai:\n{convo_text}\n\n"
        "Tom tat:"
    )

    if OllamaProvider.is_available():
        try:
            import httpx
            async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
                response = await client.post(
                    f"{settings.ollama_base_url.rstrip('/')}/api/generate",
                    json={
                        "model": settings.ollama_model,
                        "prompt": summary_prompt,
                        "stream": False,
                        "options": {"temperature": 0.3, "num_predict": 200},
                    },
                )
                response.raise_for_status()
                summary_text = str(response.json().get("response", "")).strip()
                if summary_text:
                    return SummarizeResponse(
                        summary=summary_text,
                        topics_covered=payload.lesson_topic,
                        mastery_score=0.5,
                    )
        except Exception:
            pass

    fallback = f"Buoi hoc ve '{payload.lesson_topic}' voi {len(payload.session_turns)} luot trao doi."
    return SummarizeResponse(
        summary=fallback,
        topics_covered=payload.lesson_topic,
        mastery_score=0.5,
    )

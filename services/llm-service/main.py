import os

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="LumiEdu LLM Service")


class LLMRequest(BaseModel):
    transcript: str = Field(default="")
    learner_level: str = "grade6"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "llm"}


@app.post("/respond")
async def respond(payload: LLMRequest) -> dict[str, str]:
    transcript = payload.transcript.strip()
    if not transcript:
        return {"assistant_response": "Con dang gap bai nao? Minh se goi y tung buoc nhe."}

    ollama_url = os.getenv("OLLAMA_BASE_URL", "").strip()
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    if ollama_url:
        prompt = (
            "Ban la gia su Toan lop 6 kieu Socratic. "
            "Khong dua dap an truc tiep, chi goi y tung buoc ngan gon. "
            f"Hoc sinh noi: {transcript}"
        )
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{ollama_url.rstrip('/')}/api/generate",
                json={"model": ollama_model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            model_response = str(response.json().get("response", "")).strip()
            if model_response:
                return {"assistant_response": model_response}

    return {
        "assistant_response": (
            "Minh hieu cau hoi cua con. Thu thu voi buoc 1: xac dinh de bai dang hoi dieu gi, "
            "sau do noi cho minh cach con se bat dau."
        )
    }

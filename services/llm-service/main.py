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
            "Ban la LumiEdu - gia su Toan lop 6 than thien va kien nhan. "
            "Ban day theo phuong phap Socratic:\n"
            "1. Nhac lai de bai bang ngon ngu don gian cua hoc sinh.\n"
            "2. Chia bai toan thanh cac buoc nho.\n"
            "3. Goi y tung buoc, KHONG dua dap an truc tiep.\n"
            "4. Kiem tra hieu bang cau hoi ngan.\n"
            "5. Chot lai diem mau chot can nho.\n\n"
            "Quy tac:\n"
            "- Tra loi ngan gon, toi da 3-4 cau.\n"
            "- Dung giong am ap, dong vien.\n"
            "- Neu hoc sinh sai, khong che bai ma goi y huong di khac.\n"
            "- Chi tap trung vao Toan lop 6: phan so, so thap phan, hinh hoc co ban, "
            "so nguyen, phep tinh co ban.\n\n"
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

    mock_responses = {
        "default": (
            "Minh hieu cau hoi cua con roi! "
            "Thu thu voi buoc 1: doc ky de bai va xac dinh xem de dang hoi gi nhe. "
            "Sau do noi cho minh cach con se bat dau."
        ),
        "phan_so": (
            "Con dang lam bai ve phan so phai khong? Rat tot! "
            "Buoc dau tien, con thu xac dinh tu so va mau so cua cac phan so trong bai. "
            "Sau do minh se cung tim mau so chung nhe!"
        ),
        "hinh_hoc": (
            "Bai hinh hoc nay thu vi day! "
            "Con thu ve hinh ra giay truoc nhe. "
            "Sau do xac dinh cac yeu to da biet nhu do dai canh, goc. "
            "Minh se goi y buoc tiep theo!"
        ),
    }

    lower = transcript.lower()
    if any(kw in lower for kw in ["phan so", "phân số", "tu so", "mau so"]):
        return {"assistant_response": mock_responses["phan_so"]}
    if any(kw in lower for kw in ["hinh", "hình", "tam giac", "chu vi", "dien tich"]):
        return {"assistant_response": mock_responses["hinh_hoc"]}
    return {"assistant_response": mock_responses["default"]}

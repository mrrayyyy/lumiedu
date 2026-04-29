# LumiEdu

Gia su AI voice-first cho Toan lop 6 - Hoc qua giong noi tieng Viet.

LumiEdu la nen tang gia su AI tu host, su dung phuong phap Socratic de huong dan hoc sinh giai toan qua hoi thoai giong noi. He thong xu ly toan bo pipeline STT -> LLM -> TTS trong moi truong Docker tu quan ly.

## Tinh nang chinh

- **Voice-first**: Hoc sinh noi cau hoi, AI tra loi bang giong noi tieng Viet
- **Phuong phap Socratic**: Goi mo tu tung buoc, khong dua dap an ngay
- **Self-hosted**: Toan bo du lieu nam trong ha tang so huu, bao mat hoc sinh
- **6 chu de Toan lop 6**: Phan so, So thap phan, So nguyen, Hinh hoc, Phep tinh, Ti so
- **Theo doi tien do**: Dashboard cho giao vien/phu huynh theo doi qua trinh hoc
- **Low-latency**: Pipeline toi uu cho hoi thoai tu nhien (muc tieu P95 < 2s)

## Kien truc

```
                    ┌─────────────────────────────────┐
                    │          Nginx (port 80)         │
                    │   Reverse Proxy + Audio Cache    │
                    └────┬──────────┬──────────┬───────┘
                         │          │          │
              ┌──────────▼───┐ ┌───▼────┐ ┌───▼──────────┐
              │   Frontend   │ │  API   │ │ /audio/ proxy│
              │  Next.js     │ │FastAPI │ │  -> TTS      │
              │  (port 3000) │ │(:8000) │ │              │
              └──────────────┘ └───┬────┘ └──────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
              ┌─────▼─────┐ ┌────▼─────┐ ┌─────▼─────┐
              │    STT    │ │   LLM    │ │    TTS    │
              │  Whisper  │ │  Ollama  │ │   gTTS    │
              │  (:8101)  │ │  (:8102) │ │  (:8103)  │
              └───────────┘ └──────────┘ └───────────┘
                    │              │              │
              ┌─────▼──────────────▼──────────────▼─────┐
              │         PostgreSQL + Redis               │
              └─────────────────────────────────────────┘
```

## Cau truc du an

```
lumiedu/
├── apps/
│   ├── api/                    # FastAPI backend - orchestrator
│   │   ├── core/               # Database, rate limiting, session manager
│   │   ├── repos/              # Data access layer (PostgreSQL)
│   │   ├── routers/            # REST/WebSocket endpoints
│   │   ├── auth.py             # JWT authentication
│   │   ├── config.py           # Pydantic Settings
│   │   ├── schemas.py          # Request/Response models
│   │   ├── services.py         # VoiceOrchestrator (STT->LLM->TTS)
│   │   └── main.py             # App factory + lifespan
│   └── frontend/               # Next.js web interface
│       ├── app/                # Pages (login, dashboard, session, progress)
│       ├── components/         # React components (chat/, ui/)
│       └── lib/                # API client, auth context, hooks
├── services/
│   ├── stt-service/            # Speech-to-Text (Faster-Whisper)
│   │   ├── config/             # Settings
│   │   ├── providers/          # WhisperProvider, ExternalProvider
│   │   └── schemas/            # STT request/response models
│   ├── llm-service/            # Language Model (Ollama)
│   │   ├── config/             # Settings + Socratic prompts
│   │   ├── providers/          # OllamaProvider, MockProvider
│   │   └── schemas/            # LLM request/response models
│   └── tts-service/            # Text-to-Speech (gTTS)
│       ├── config/             # Settings
│       ├── providers/          # GTTSProvider, ExternalProvider
│       └── schemas/            # TTS request/response models
├── infra/
│   ├── nginx/                  # Reverse proxy config
│   └── scripts/                # Backup, restore, smoke test
├── docs/                       # Documentation
├── docker-compose.yml          # Full stack orchestration
└── .env.example                # Environment variables template
```

## Bat dau nhanh

### Yeu cau

- Docker >= 20.10
- Docker Compose >= 2.0
- 4GB RAM toi thieu (Whisper model + services)

### Cai dat va chay

```bash
# 1. Clone repository
git clone https://github.com/mrrayyyy/lumiedu.git
cd lumiedu

# 2. Tao file cau hinh
cp .env.example .env

# 3. Build va khoi dong
docker compose up --build -d

# 4. Doi tat ca services healthy (~2 phut)
docker compose ps

# 5. Truy cap ung dung
# http://localhost
```

### Dang nhap

Tai khoan admin duoc tao tu dong khi khoi dong:
- **Email:** `admin@lumiedu.local`
- **Password:** `Admin123!`

### Su dung

1. **Dang nhap** tai `http://localhost/login`
2. **Tao phien hoc**: Click "Phien hoc moi" -> Chon chu de -> "Bat dau hoc"
3. **Hoc**: Go cau hoi hoac nhan mic de noi -> AI tra loi bang text + giong noi
4. **Xem tien do**: Click "Tien do" trong sidebar

## Luong du lieu voice

```
Hoc sinh noi/go cau hoi
         │
         ▼
    ┌─────────┐     ┌──────────┐     ┌─────────┐
    │   STT   │────▶│   LLM    │────▶│   TTS   │
    │ Whisper │     │  Ollama  │     │  gTTS   │
    │ Audio   │     │ Socratic │     │  Audio  │
    │ -> Text │     │  Prompt  │     │ <- Text │
    └─────────┘     └──────────┘     └─────────┘
                                          │
                                          ▼
                                   Hoc sinh nghe
                                   phan hoi AI
```

1. **STT**: Nhan audio tu mic, chuyen thanh text (Faster-Whisper, tieng Viet)
2. **LLM**: Nhan text + lich su hoi thoai + chu de -> tra loi theo phuong phap Socratic
3. **TTS**: Chuyen text phan hoi thanh audio tieng Viet (gTTS)
4. **API** orchestrate toan bo voi retry logic va exponential backoff

## Cau hinh

Xem `.env.example` de biet toan bo bien moi truong. Mot so cau hinh quan trong:

| Bien | Mo ta | Mac dinh |
|------|-------|----------|
| `WHISPER_MODEL_SIZE` | Kich thuoc model Whisper (tiny/base/small/medium) | `base` |
| `OLLAMA_BASE_URL` | URL Ollama server (de trong = mock mode) | _(trong)_ |
| `OLLAMA_MODEL` | Model LLM su dung | `llama3.2:3b` |
| `TTS_GTTS_LANGUAGE` | Ngon ngu TTS | `vi` |
| `AUTH_DISABLED` | Tat xac thuc (development) | `false` |
| `MAX_CONCURRENT_SESSIONS` | So phien dong thoi toi da | `3` |

### Mock mode

Khi khong co Ollama (`OLLAMA_BASE_URL` trong), LLM service tu dong dung mock responses. Phu hop de test UI va pipeline ma khong can GPU/LLM server.

## Phat trien

Xem [docs/development.md](docs/development.md) de biet cach setup moi truong phat trien.

## Tham khao

- [Kien truc chi tiet](docs/architecture.md)
- [API Endpoints](docs/api.md)
- [Huong dan phat trien](docs/development.md)
- [Huong dan trien khai](docs/deployment.md)
- [Ho so san pham goc](docs/superpowers/specs/2026-04-23-lumiedu-build-ready-dossier.md)

## Stack cong nghe

| Thanh phan | Cong nghe |
|-----------|-----------|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend API | FastAPI, Python, asyncio, httpx |
| STT | Faster-Whisper (CTranslate2) |
| LLM | Ollama (Llama 3.2 / Mistral) |
| TTS | gTTS (Google Text-to-Speech) |
| Database | PostgreSQL 16, async SQLAlchemy |
| Cache | Redis 7 |
| Proxy | Nginx 1.27 |
| Container | Docker, Docker Compose |

## License

Private - All rights reserved.

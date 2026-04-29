# Huong dan phat trien

## Yeu cau

- Docker >= 20.10
- Docker Compose >= 2.0
- Node.js 20+ (neu phat trien frontend ngoai Docker)
- Python 3.11+ (neu phat trien backend ngoai Docker)
- 4GB RAM toi thieu

## Setup nhanh (Docker - khuyen nghi)

```bash
# Clone va setup
git clone https://github.com/mrrayyyy/lumiedu.git
cd lumiedu
cp .env.example .env

# Build va chay toan bo stack
docker compose up --build -d

# Kiem tra trang thai
docker compose ps          # Tat ca should be "healthy"
docker compose logs -f     # Xem logs realtime

# Truy cap
# http://localhost          - Frontend
# http://localhost/api/health - API health check
```

## Setup phat trien tung thanh phan

### Frontend (ngoai Docker)

```bash
cd apps/frontend
npm install
npm run dev
# -> http://localhost:3000
```

Luu y: Frontend goi API qua `/api` (relative path). Khi chay ngoai Docker, can nginx hoac proxy de route `/api` toi backend.

### Backend API (ngoai Docker)

```bash
cd apps/api
pip install -r requirements.txt

# Can PostgreSQL va Redis dang chay
export DATABASE_URL=postgresql+asyncpg://lumiedu:change_me@localhost:5432/lumiedu
export REDIS_URL=redis://localhost:6379/0
export STT_URL=http://localhost:8101
export LLM_URL=http://localhost:8102
export TTS_URL=http://localhost:8103

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Microservices (ngoai Docker)

```bash
# STT Service
cd services/stt-service
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8101

# LLM Service
cd services/llm-service
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8102

# TTS Service
cd services/tts-service
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8103
```

## Cau truc code

### Backend API - Phan lop

```
Routers  ->  Services  ->  Repos  ->  Database
  │              │            │           │
  │    VoiceOrchestrator      │     PostgreSQL
  │    SessionManager         │     (async SQLAlchemy)
  │              │            │
  │         Calls to:         │
  │     STT/LLM/TTS services  │
  └────────────────────────────┘
```

- **Routers** (`routers/`): Dinh nghia HTTP endpoints, validation, auth
- **Services** (`services.py`): Business logic, voice pipeline orchestration
- **Repos** (`repos/`): Data access, SQL queries
- **Core** (`core/`): Database engine, Redis, rate limiting, session manager

### Microservices - Provider pattern

Moi service co cau truc giong nhau:
```
service/
├── config/
│   ├── __init__.py
│   └── settings.py       # Configuration tu env vars
├── providers/
│   ├── __init__.py
│   ├── primary.py         # Provider chinh (Whisper/Ollama/gTTS)
│   └── external.py        # Fallback provider
├── schemas/
│   ├── __init__.py
│   └── models.py          # Pydantic request/response models
├── main.py                # FastAPI app, endpoints, fallback chain
├── requirements.txt
└── Dockerfile
```

De them provider moi:
1. Tao file trong `providers/`
2. Implement `is_available()` static method
3. Implement method chinh (transcribe/chat/synthesize)
4. Them vao fallback chain trong `main.py`

### Frontend - Component architecture

```
app/                        # Pages (route-based)
├── (app)/                  # Route group co Sidebar layout
│   ├── dashboard/          # /dashboard
│   └── progress/           # /progress
├── login/                  # /login (khong co sidebar)
└── session/                # /session?id=... (full-screen chat)

components/
├── chat/                   # Chat-specific components
│   ├── chat-bubble.tsx     # Tin nhan (learner/tutor) + audio play
│   ├── chat-input.tsx      # Text input + mic button + send
│   ├── session-header.tsx  # Topic, learner ID, WS status, end button
│   └── typing-indicator.tsx
├── ui/                     # Reusable UI components
│   ├── loading-spinner.tsx
│   ├── error-alert.tsx
│   ├── stat-card.tsx       # Dashboard metric card
│   └── session-card.tsx    # Session list item
├── sidebar.tsx             # Navigation sidebar
└── icons.tsx               # SVG icon components

lib/
├── api.ts                  # Centralized API client (fetch wrapper)
├── auth-context.tsx        # React Context cho JWT + localStorage
├── types.ts                # TypeScript interfaces
└── hooks/
    ├── use-require-auth.ts # Redirect neu chua login
    ├── use-poll.ts         # Polling hook (metrics refresh)
    └── use-voice-recorder.ts # Web Audio API recording
```

## Cac lenh huu ich

```bash
# Xem logs cua 1 service
docker compose logs -f api
docker compose logs -f tts-service

# Restart 1 service
docker compose restart api

# Rebuild 1 service
docker compose up --build -d frontend

# Kiem tra health cua services
curl http://localhost/api/health
curl http://localhost:8101/health    # STT
curl http://localhost:8102/health    # LLM
curl http://localhost:8103/health    # TTS

# Truy cap PostgreSQL
docker compose exec postgres psql -U lumiedu -d lumiedu

# Xem Redis
docker compose exec redis redis-cli

# Frontend lint
cd apps/frontend && npm run lint

# Frontend build
cd apps/frontend && npm run build
```

## Bien moi truong

Xem `.env.example` de biet toan bo bien. Mot so luu y:

- `AUTH_DISABLED=true` - Tat auth de test nhanh (khong can login)
- `OLLAMA_BASE_URL=` - De trong = dung mock LLM (khong can Ollama)
- `WHISPER_MODEL_SIZE=tiny` - Dung model nho khi test (nhanh hon, it RAM)
- `TTS_GTTS_SLOW=true` - Doc cham hon de hoc sinh nghe ro

## Quy trinh phat trien

1. Tao branch tu `main`
2. Code + test local voi `docker compose up --build`
3. Chay lint: `cd apps/frontend && npm run lint`
4. Tao PR vao `main`
5. Review + merge

## Troubleshooting

### Services khong healthy

```bash
docker compose ps                    # Xem status
docker compose logs <service-name>   # Xem error logs
```

### STT service khoi dong cham

Lan dau chay, Whisper se download model (~150MB cho base). Doi 2-3 phut.

### LLM tra ve mock responses

`OLLAMA_BASE_URL` trong hoac Ollama khong chay. De dung Ollama that:
1. Cai dat Ollama: https://ollama.ai
2. Chay: `ollama pull llama3.2:3b`
3. Set `OLLAMA_BASE_URL=http://host.docker.internal:11434` trong `.env`

### Frontend build fail

```bash
cd apps/frontend
rm -rf node_modules .next
npm install
npm run build
```

### Audio khong play duoc

Kiem tra nginx co proxy `/audio/` toi TTS service:
```bash
curl -v http://localhost/audio/test.mp3
docker compose logs reverse-proxy | grep audio
```

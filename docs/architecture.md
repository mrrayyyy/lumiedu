# Kien truc LumiEdu

## Tong quan

LumiEdu su dung kien truc microservices, toan bo chay trong Docker Compose. He thong gom 8 containers hoat dong doc lap, giao tiep qua HTTP noi bo.

## So do kien truc

```
Client (Browser)
       │
       ▼
┌──────────────────────────────────────────────────┐
│                 Nginx (port 80)                  │
│  Reverse Proxy - Routing - WebSocket Upgrade     │
│                                                  │
│  /          -> Frontend (3000)                   │
│  /api/      -> API (8000)                        │
│  /audio/    -> TTS Service (8103)                │
│  /health    -> API (8000)                        │
│  /metrics   -> API (8000)                        │
└──────┬───────────┬───────────┬───────────────────┘
       │           │           │
┌──────▼──┐  ┌─────▼──┐  ┌────▼─────┐
│Frontend │  │  API   │  │TTS Audio │
│Next.js  │  │FastAPI │  │ Static   │
│   UI    │  │Orchest.│  │  Files   │
└─────────┘  └───┬────┘  └──────────┘
                 │
      ┌──────────┼──────────┐
      │          │          │
┌─────▼───┐ ┌───▼────┐ ┌───▼─────┐
│   STT   │ │  LLM   │ │   TTS   │
│ Whisper │ │ Ollama │ │  gTTS   │
│ :8101   │ │ :8102  │ │  :8103  │
└─────────┘ └────────┘ └─────────┘
      │          │          │
┌─────▼──────────▼──────────▼─────┐
│    PostgreSQL 16  │   Redis 7   │
│    :5432          │   :6379     │
└───────────────────┴─────────────┘
```

## Cac thanh phan

### 1. Nginx Reverse Proxy

- **Port:** 80
- **Vai tro:** Gateway duy nhat cho client, routing tat ca request
- **Dac biet:**
  - WebSocket upgrade cho `/api/v1/sessions/` (hoi thoai realtime)
  - Audio proxy `/audio/` -> TTS service (cache 1h)
  - Proxy timeout 300s cho voice pipeline

### 2. Frontend (Next.js)

- **Port:** 3000
- **Framework:** Next.js 16, React 19, TypeScript, Tailwind CSS
- **Cau truc:**
  ```
  app/
  ├── (app)/              # Route group voi Sidebar layout
  │   ├── dashboard/      # Trang chu - metrics, sessions, tao phien
  │   ├── progress/       # Theo doi tien do hoc sinh
  │   └── layout.tsx      # Sidebar + main content layout
  ├── login/              # Trang dang nhap (khong co sidebar)
  ├── session/            # Giao dien chat tutoring (full-screen)
  └── layout.tsx          # Root layout (AuthProvider)
  
  components/
  ├── chat/               # ChatBubble, ChatInput, SessionHeader, TypingIndicator
  ├── ui/                 # LoadingSpinner, ErrorAlert, StatCard, SessionCard
  ├── sidebar.tsx         # Navigation sidebar
  └── icons.tsx           # SVG icon components
  
  lib/
  ├── api.ts              # Centralized API client
  ├── auth-context.tsx    # JWT auth state management
  ├── types.ts            # TypeScript type definitions
  └── hooks/              # useRequireAuth, usePoll, useVoiceRecorder
  ```

### 3. API Backend (FastAPI)

- **Port:** 8000
- **Framework:** FastAPI, Python 3.11, asyncio
- **Vai tro:** Orchestrator trung tam - quan ly sessions, dieu phoi voice pipeline
- **Cau truc phan lop:**
  ```
  Routers (HTTP/WS)  ->  Services (business logic)  ->  Repos (data access)
       │                       │                            │
  auth_router.py         services.py               session_repo.py
  sessions.py           (VoiceOrchestrator)         user_repo.py
  progress.py                                      progress_repo.py
  health.py
  ```
- **Core modules:**
  - `config.py` - Pydantic Settings, auto-load tu env vars
  - `auth.py` - JWT token creation/verification, PBKDF2 password hashing
  - `core/database.py` - async SQLAlchemy engine, Redis client
  - `core/session_manager.py` - In-memory session state + WebSocket broadcast
  - `core/rate_limit.py` - Redis-based rate limiting

### 4. STT Service (Faster-Whisper)

- **Port:** 8101
- **Provider pattern:**
  1. **WhisperProvider** (primary) - Faster-Whisper local, VAD filter, beam search
  2. **ExternalProvider** (fallback) - External STT API
  3. Mock fallback - Tra ve text "khong nhan dien duoc"
- **Config:** Model size (tiny/base/small/medium), device (cpu/cuda), compute type (int8/float16)

### 5. LLM Service (Ollama)

- **Port:** 8102
- **Provider pattern:**
  1. **OllamaProvider** (primary) - Ollama local, conversation history (10 turns), Socratic prompt
  2. **MockProvider** (fallback) - Responses tieng Viet theo chu de
- **Socratic prompt:** System prompt chi tiet yeu cau AI:
  - Goi mo tu tung buoc thay vi dua dap an
  - Kiem tra hieu biet bang cau hoi ngan
  - Phan hoi bang tieng Viet don gian, phu hop lop 6
- **Chu de ho tro:** phan_so, so_thap_phan, so_nguyen, hinh_hoc, phep_tinh, ti_so

### 6. TTS Service (gTTS)

- **Port:** 8103
- **Provider pattern:**
  1. **ExternalProvider** - External TTS API (GPT-SoVITS, etc.)
  2. **GTTSProvider** - Google TTS tieng Viet, LRU cache
  3. Mock fallback
- **Audio files:** Luu trong cache directory, serve qua FastAPI StaticFiles tai `/audio/`
- **Cache:** MD5 hash text lam filename, LRU eviction khi vuot `TTS_MAX_CACHE_FILES`

### 7. PostgreSQL

- **Port:** 5432
- **Tables:** users, learning_sessions, session_turns
- **ORM:** async SQLAlchemy voi raw SQL queries
- **Bootstrap:** Tu dong tao admin user khi khoi dong

### 8. Redis

- **Port:** 6379
- **Su dung:**
  - Rate limiting (login, session creation)
  - Session state cache (tuong lai)

## Luong Voice Pipeline

```
1. Client gui request (text hoac audio base64)
         │
2. API VoiceOrchestrator.run_turn()
         │
3. Co audio? ──Yes──> STT: POST /transcribe
         │                    │
         No                   ▼
         │              Text transcript
         │                    │
         ▼                    ▼
4. LLM: POST /chat
   (text + history + topic + Socratic prompt)
         │
         ▼
5. TTS: POST /synthesize
   (LLM response text -> audio file)
         │
         ▼
6. API tra ve: { transcript, assistant_response, audio_url, response_ms }
         │
         ▼
7. Client hien thi text + play audio qua /audio/ proxy
```

### Retry Logic

VoiceOrchestrator su dung exponential backoff cho moi buoc:
- Max 2 retries, delay 0.5s -> 1s
- Neu STT fail -> dung text_input lam transcript
- Neu LLM fail -> tra ve message loi
- Neu TTS fail -> tra ve response khong co audio

## Mo rong

### Them provider moi

1. Tao file trong `providers/` cua service tuong ung
2. Implement `is_available()` va method chinh (transcribe/chat/synthesize)
3. Them vao fallback chain trong `main.py`

### Them endpoint moi

1. Tao file trong `apps/api/routers/`
2. Tao schemas trong `apps/api/schemas.py`
3. Tao queries trong `apps/api/repos/`
4. Register router trong `apps/api/main.py`

### Them trang frontend moi

1. Tao thu muc trong `apps/frontend/app/(app)/` (co sidebar) hoac `app/` (full-screen)
2. Tao components trong `components/`
3. Them nav link trong `components/sidebar.tsx`

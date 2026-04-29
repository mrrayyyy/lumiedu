# API Endpoints

Base URL: `/api`

Tat ca endpoints (tru login va health) yeu cau JWT token trong header:
```
Authorization: Bearer <access_token>
```

## Authentication

### POST /api/v1/auth/login

Dang nhap va nhan JWT token.

**Request:**
```json
{
  "email": "admin@lumiedu.local",
  "password": "Admin123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Rate limit:** 10 attempts / 5 phut (theo email + IP)

---

## Sessions

### POST /api/v1/sessions

Tao phien hoc moi.

**Request:**
```json
{
  "learner_id": "student-001",
  "lesson_topic": "Phan so lop 6"
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "learner_id": "student-001",
  "lesson_topic": "Phan so lop 6",
  "status": "active",
  "created_at": "2026-04-29T03:14:00Z"
}
```

**Rate limit:** 20 requests / 5 phut  
**Loi 429:** Khi dat `MAX_CONCURRENT_SESSIONS` (mac dinh: 3)

### GET /api/v1/sessions

Danh sach phien hoc.

**Query params:**
- `learner_id` (optional) - Loc theo ma hoc sinh

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "learner_id": "student-001",
      "lesson_topic": "Phan so lop 6",
      "status": "active",
      "created_at": "2026-04-29T03:14:00Z"
    }
  ],
  "total": 1
}
```

### GET /api/v1/sessions/{session_id}

Chi tiet mot phien hoc.

**Response:** `SessionResponse` (giong tren)  
**Loi 404:** Session khong ton tai hoac da ket thuc

### POST /api/v1/sessions/{session_id}/end

Ket thuc phien hoc.

**Response:**
```json
{
  "status": "ended",
  "session_id": "uuid"
}
```

### GET /api/v1/sessions/{session_id}/turns

Lich su hoi dap cua phien hoc.

**Response:**
```json
[
  {
    "transcript": "1/2 + 1/3 bang bao nhieu?",
    "assistant_response": "De minh huong dan con nhe...",
    "created_at": "2026-04-29T03:15:00Z"
  }
]
```

### POST /api/v1/sessions/{session_id}/turns

Gui cau hoi va nhan phan hoi tu AI. Day la endpoint chinh cua voice pipeline.

**Request:**
```json
{
  "text_input": "1/2 + 1/3 bang bao nhieu?",
  "audio_base64": null
}
```

- `text_input`: Cau hoi dang text (bat buoc neu khong co audio)
- `audio_base64`: Audio file encoded base64 (gui tu mic recording)

**Response:**
```json
{
  "session_id": "uuid",
  "transcript": "1/2 + 1/3 bang bao nhieu?",
  "assistant_response": "Rat tot! De tinh 1/2 + 1/3, con can tim mau so chung...",
  "audio_url": "/audio/abc123def456.mp3",
  "response_ms": 306
}
```

- `transcript`: Text tu STT (hoac text_input neu khong co audio)
- `assistant_response`: Phan hoi cua AI theo phuong phap Socratic
- `audio_url`: URL file audio phan hoi (truy cap qua nginx `/audio/` proxy)
- `response_ms`: Thoi gian xu ly toan bo pipeline (ms)

### WebSocket /api/v1/sessions/{session_id}/ws

Ket noi WebSocket cho phien hoc (realtime status).

**Query params:**
- `token` - JWT access token

**Events:**
- Server gui: `pong` (phan hoi ping)
- Client gui: `ping` (heartbeat)

---

## Progress

### GET /api/v1/progress/{learner_id}

Tien do hoc tap cua hoc sinh.

**Response:**
```json
{
  "learner_id": "student-001",
  "total_sessions": 5,
  "total_turns": 23,
  "avg_latency_ms": 0,
  "topics_studied": ["Phan so lop 6", "So nguyen"],
  "recent_sessions": [
    {
      "session_id": "uuid",
      "learner_id": "student-001",
      "lesson_topic": "Phan so lop 6",
      "status": "ended",
      "created_at": "2026-04-29T03:14:00Z"
    }
  ]
}
```

---

## Health & Metrics

### GET /health

Kiem tra trang thai he thong.

**Response:**
```json
{
  "status": "ok",
  "environment": "development",
  "dependencies": {
    "postgres": "ok",
    "redis": "ok"
  }
}
```

### GET /metrics

So lieu hoat dong.

**Response:**
```json
{
  "turn_total": 15,
  "turn_error_total": 1,
  "e2e_latency_ms_last": 306
}
```

---

## Microservice Internal APIs

Cac API noi bo giua API backend va microservices (khong expose ra ngoai).

### STT Service (port 8101)

**POST /transcribe**
```json
// Request (multipart/form-data)
{
  "file": "<audio file>"
}

// Response
{
  "text": "mot phan hai cong mot phan ba",
  "confidence": 0.92,
  "language": "vi",
  "duration_ms": 450,
  "provider": "whisper"
}
```

### LLM Service (port 8102)

**POST /chat**
```json
// Request
{
  "message": "1/2 + 1/3 bang bao nhieu?",
  "lesson_topic": "phan_so",
  "history": [
    {"role": "learner", "text": "..."},
    {"role": "tutor", "text": "..."}
  ]
}

// Response
{
  "response": "Rat hay! De cong hai phan so...",
  "tokens_used": 150,
  "duration_ms": 800,
  "provider": "ollama"
}
```

### TTS Service (port 8103)

**POST /synthesize**
```json
// Request
{
  "text": "Rat hay! De cong hai phan so...",
  "language": "vi",
  "voice": "default"
}

// Response
{
  "audio_url": "/audio/abc123.mp3",
  "text": "Rat hay! De cong hai phan so...",
  "duration_ms": 350,
  "provider": "gtts"
}
```

Audio files duoc serve tai `http://tts-service:8103/audio/` (noi bo) va `http://localhost/audio/` (qua nginx).

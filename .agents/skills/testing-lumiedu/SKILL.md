# Testing LumiEdu Application

## Overview
LumiEdu is a voice-first AI tutoring platform for Grade 6 Math in Vietnamese. It runs as a Docker Compose stack with 8 services.

## Devin Secrets Needed
No secrets required - the app uses a bootstrap admin account for testing.

## Prerequisites
- Docker and Docker Compose must be available
- No external API keys needed (services run in mock/local mode)

## Setup

```bash
cd /home/ubuntu/repos/lumiedu
cp .env.example .env
docker compose up --build -d
# Wait ~2 minutes for all services to build and start
```

## Verify Services Are Healthy

All 8 containers should be running and healthy:
```bash
docker compose ps  # All should show "healthy"
curl -s http://localhost/api/health | python3 -m json.tool  # postgres: ok, redis: ok
curl -s http://localhost:8101/health  # STT: whisper_available: yes
curl -s http://localhost:8102/health  # LLM: ollama_configured: no (mock mode)
curl -s http://localhost:8103/health  # TTS: gtts_available: yes
```

## Test Credentials
- **Email:** `admin@lumiedu.local`
- **Password:** `Admin123!`
- These are pre-filled on the login page at `http://localhost/login`

## Key Test Flows

### 1. Login Flow
- Navigate to `http://localhost` -> auto-redirects to `/login`
- Credentials are pre-filled, click "Dang nhap"
- Verify redirect to `/dashboard`

### 2. Session Creation & Text Chat
- On dashboard, click "Phien hoc moi" to expand form
- Click a topic chip (e.g., "Phan so lop 6") to fill the topic field
- Click "Bat dau hoc" to create session
- Type a math question and press Enter
- Tutor responds with text + audio play button (if TTS generated audio)
- Response shows latency in ms

### 3. TTS Audio Playback
- After a tutor response, a blue play button appears next to "LumiEdu" label
- The play button only appears if `audioUrl` doesn't contain `/mock/`
- Audio is served via nginx `/audio/` proxy -> TTS service at port 8103
- Verify with: `curl -s -o /dev/null -w "%{http_code}" http://localhost/audio/<filename>.mp3`

### 4. Progress Page
- Navigate to `/progress` (or click "Tien do" in sidebar)
- Data loads automatically for "student-demo"
- Search is triggered by clicking "Xem tien do" button, NOT on keystroke

### 5. End Session
- Click "Ket thuc" (red button) in session header
- Redirects to dashboard, session shows "Da ket thuc"

## Known Limitations

### Voice Recording Cannot Be Tested in Devin Environment
The test VM has no microphone hardware or PulseAudio, so `navigator.mediaDevices.getUserMedia()` fails silently. The mic button click has no visible effect. To test voice recording:
- Use a real browser with mic access, OR
- Write a Playwright test that mocks `getUserMedia` with a synthetic audio stream

### LLM Runs in Mock Mode
Without Ollama installed, the LLM service returns generic mock responses (not topic-specific Socratic tutoring). The mock response is: "Chao con! Minh la LumiEdu, gia su Toan lop 6 cua con..."

### WebSocket Status
The session page shows WebSocket connection status ("Ket noi" = connected, green dot). This connects automatically when a session is opened.

## Service Architecture
- **nginx** (port 80): Reverse proxy for frontend, API, and `/audio/` to TTS
- **frontend** (port 3000): Next.js app
- **api** (port 8000): FastAPI orchestrator
- **stt-service** (port 8101): Faster-Whisper
- **llm-service** (port 8102): Ollama wrapper (mock if no Ollama)
- **tts-service** (port 8103): gTTS Vietnamese
- **postgres** (port 5432): User/session data
- **redis** (port 6379): Session cache

## Tips
- The dashboard has a "Lam moi" (refresh) link next to "Phien hoc gan day" - use it to reload session list without page refresh
- Session page doesn't have the sidebar - navigate back using the back arrow or browser back
- Frontend image is ~569MB with multi-stage Docker build
- If docker-compose build fails, check disk space - Whisper model download can be large

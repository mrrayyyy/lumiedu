from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware

from auth import create_access_token, decode_access_token, get_current_user_email, verify_password
from config import settings
from db import (
    close_connections,
    ensure_db_ready,
    get_user_credentials,
    ping_dependencies,
    redis_client,
    save_session,
    save_turn,
)
from schemas import LoginRequest, SessionCreateRequest, SessionResponse, TokenResponse, TurnRequest, TurnResponse
from services import VoiceOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("lumiedu-api")

app = FastAPI(title=settings.app_name)
orchestrator = VoiceOrchestrator()
active_sessions: dict[str, SessionResponse] = {}
session_connections: dict[str, set[WebSocket]] = {}
metrics = {"turn_total": 0, "turn_error_total": 0, "e2e_latency_ms_last": 0}

allowed_origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    await ensure_db_ready()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await orchestrator.close()
    await close_connections()


@app.get("/health")
async def health() -> dict[str, object]:
    deps = await ping_dependencies()
    return {"status": "ok", "environment": settings.app_env, "dependencies": deps}


@app.get("/api/health")
async def api_health() -> dict[str, object]:
    return await health()


@app.get("/metrics")
async def get_metrics(_: str = Depends(get_current_user_email)) -> dict[str, int]:
    return metrics


@app.get("/api/metrics")
async def api_metrics(user_email: str = Depends(get_current_user_email)) -> dict[str, int]:
    _ = user_email
    return metrics


@app.post("/api/v1/sessions", response_model=SessionResponse)
async def create_session(
    payload: SessionCreateRequest,
    request: Request,
    user_email: str = Depends(get_current_user_email),
) -> SessionResponse:
    await _check_rate_limit(
        key=f"ratelimit:session-create:{user_email}:{request.client.host if request.client else 'unknown'}",
        limit=settings.session_create_rate_limit,
        window_seconds=settings.session_create_rate_window_seconds,
        detail="Too many session creation attempts. Please try again later.",
    )

    if len(active_sessions) >= settings.max_concurrent_sessions:
        raise HTTPException(status_code=429, detail="Max concurrent sessions reached")

    session = SessionResponse(
        session_id=str(uuid4()),
        learner_id=payload.learner_id,
        lesson_topic=payload.lesson_topic,
        created_at=datetime.now(UTC),
        status="active",
    )
    active_sessions[session.session_id] = session
    session_connections[session.session_id] = set()
    await save_session(session.session_id, session.learner_id, session.lesson_topic, session.status)
    try:
        await redis_client.set(f"session:{session.session_id}:status", session.status, ex=3600)
    except Exception:
        logger.warning("redis_session_write_failed", extra={"session_id": session.session_id})
    logger.info("session_created", extra={"session_id": session.session_id, "user_email": user_email})
    return session


@app.post("/api/v1/sessions/{session_id}/turns", response_model=TurnResponse)
async def process_turn(
    session_id: str, payload: TurnRequest, user_email: str = Depends(get_current_user_email)
) -> TurnResponse:
    session = active_sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        result = await orchestrator.run_turn(payload.text_input)
        response = TurnResponse(
            session_id=session_id,
            transcript=str(result["transcript"]),
            assistant_response=str(result["assistant_response"]),
            audio_url=str(result["audio_url"]),
            response_ms=int(result["response_ms"]),
        )
        metrics["turn_total"] += 1
        metrics["e2e_latency_ms_last"] = response.response_ms
        await save_turn(session_id, response.transcript, response.assistant_response)
        try:
            await redis_client.set(f"session:{session_id}:last_turn_ms", response.response_ms, ex=3600)
        except Exception:
            logger.warning("redis_turn_write_failed", extra={"session_id": session_id})
        await _broadcast_event(
            session_id,
            {"type": "turn_completed", "payload": response.model_dump(), "user_email": user_email},
        )
        return response
    except Exception as exc:
        metrics["turn_error_total"] += 1
        logger.exception("turn_failed", extra={"session_id": session_id, "error": str(exc)})
        raise HTTPException(status_code=502, detail="Voice pipeline failed") from exc


@app.websocket("/api/v1/sessions/{session_id}/ws")
async def session_ws(session_id: str, websocket: WebSocket) -> None:
    auth_header = websocket.headers.get("authorization")
    token_query = websocket.query_params.get("token")
    if not settings.auth_disabled:
        token = ""
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
        elif token_query:
            token = token_query
        else:
            await websocket.close(code=4401)
            return
        try:
            decode_access_token(token)
        except HTTPException:
            await websocket.close(code=4401)
            return

    if session_id not in active_sessions:
        await websocket.close(code=4404)
        return

    await websocket.accept()
    session_connections.setdefault(session_id, set()).add(websocket)
    await websocket.send_json({"type": "connected", "session_id": session_id})
    try:
        while True:
            _ = await websocket.receive_text()
            await websocket.send_json({"type": "heartbeat", "session_id": session_id})
    except WebSocketDisconnect:
        pass
    finally:
        session_connections.get(session_id, set()).discard(websocket)


async def _broadcast_event(session_id: str, event: dict[str, object]) -> None:
    sockets = session_connections.get(session_id, set())
    closed: list[WebSocket] = []
    for websocket in sockets:
        try:
            await websocket.send_json(event)
        except Exception:
            closed.append(websocket)
    for websocket in closed:
        sockets.discard(websocket)


@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request) -> TokenResponse:
    client_host = request.client.host if request.client else "unknown"
    await _check_rate_limit(
        key=f"ratelimit:login:{payload.email}:{client_host}",
        limit=settings.login_rate_limit_attempts,
        window_seconds=settings.login_rate_limit_window_seconds,
        detail="Too many login attempts. Please try again later.",
    )

    if settings.auth_disabled:
        return TokenResponse(access_token=create_access_token(settings.bootstrap_admin_email))

    credentials = await get_user_credentials(payload.email)
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    _, password_hash = credentials
    if not verify_password(payload.password, password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(payload.email)
    return TokenResponse(access_token=token)


async def _check_rate_limit(key: str, limit: int, window_seconds: int, detail: str) -> None:
    if limit <= 0 or window_seconds <= 0:
        return
    try:
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, window_seconds)
        if current > limit:
            raise HTTPException(status_code=429, detail=detail)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("rate_limit_check_failed", extra={"key": key, "error": str(exc)})

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect

from auth import decode_access_token, get_current_user_email
from config import settings
from core.database import redis_client
from core.rate_limit import check_rate_limit
from core.session_manager import SessionManager
from repos.session_repo import get_all_sessions, get_sessions_by_learner, get_turns_by_session, save_turn
from routers.health import metrics
from schemas import (
    SessionCreateRequest,
    SessionListResponse,
    SessionResponse,
    TurnHistoryItem,
    TurnRequest,
    TurnResponse,
)
from services import VoiceOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])

session_mgr = SessionManager()
orchestrator = VoiceOrchestrator()


@router.post("", response_model=SessionResponse)
async def create_session(
    payload: SessionCreateRequest,
    request: Request,
    user_email: str = Depends(get_current_user_email),
) -> SessionResponse:
    await check_rate_limit(
        key=f"ratelimit:session-create:{user_email}:{request.client.host if request.client else 'unknown'}",
        limit=settings.session_create_rate_limit,
        window_seconds=settings.session_create_rate_window_seconds,
        detail="Too many session creation attempts. Please try again later.",
    )

    if session_mgr.active_count >= settings.max_concurrent_sessions:
        raise HTTPException(status_code=429, detail="Max concurrent sessions reached")

    session = await session_mgr.create(payload.learner_id, payload.lesson_topic)
    logger.info("session_created", extra={"session_id": session.session_id, "user_email": user_email})
    return session


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    learner_id: str | None = None,
    _user_email: str = Depends(get_current_user_email),
) -> SessionListResponse:
    rows = await get_sessions_by_learner(learner_id) if learner_id else await get_all_sessions()
    sessions = [
        SessionResponse(
            session_id=str(r["session_id"]),
            learner_id=str(r["learner_id"]),
            lesson_topic=str(r["lesson_topic"]),
            status=str(r["status"]),
            created_at=r["created_at"],
        )
        for r in rows
    ]
    for s in sessions:
        active = session_mgr.get(s.session_id)
        if active:
            s.status = active.status
    return SessionListResponse(sessions=sessions, total=len(sessions))


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    _user_email: str = Depends(get_current_user_email),
) -> SessionResponse:
    session = session_mgr.get(session_id)
    if session is not None:
        return session
    raise HTTPException(status_code=404, detail="Session not found")


@router.get("/{session_id}/turns", response_model=list[TurnHistoryItem])
async def get_session_turns(
    session_id: str,
    _user_email: str = Depends(get_current_user_email),
) -> list[TurnHistoryItem]:
    rows = await get_turns_by_session(session_id)
    return [
        TurnHistoryItem(
            transcript=str(r["transcript"]),
            assistant_response=str(r["assistant_response"]),
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.post("/{session_id}/end")
async def end_session(
    session_id: str,
    user_email: str = Depends(get_current_user_email),
) -> dict[str, str]:
    try:
        await session_mgr.end(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    logger.info("session_ended", extra={"session_id": session_id, "user_email": user_email})
    return {"status": "ended", "session_id": session_id}


@router.post("/{session_id}/turns", response_model=TurnResponse)
async def process_turn(
    session_id: str,
    payload: TurnRequest,
    user_email: str = Depends(get_current_user_email),
) -> TurnResponse:
    if not session_mgr.is_active(session_id):
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
        await session_mgr.broadcast(
            session_id,
            {"type": "turn_completed", "payload": response.model_dump(), "user_email": user_email},
        )
        return response
    except Exception as exc:
        metrics["turn_error_total"] += 1
        logger.exception("turn_failed", extra={"session_id": session_id, "error": str(exc)})
        raise HTTPException(status_code=502, detail="Voice pipeline failed") from exc


@router.websocket("/{session_id}/ws")
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

    if not session_mgr.is_active(session_id):
        await websocket.close(code=4404)
        return

    await websocket.accept()
    session_mgr.add_connection(session_id, websocket)
    await websocket.send_json({"type": "connected", "session_id": session_id})
    try:
        while True:
            _ = await websocket.receive_text()
            await websocket.send_json({"type": "heartbeat", "session_id": session_id})
    except WebSocketDisconnect:
        pass
    finally:
        session_mgr.remove_connection(session_id, websocket)

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect

import httpx

from auth import (
    CurrentUser,
    ROLE_ADMIN,
    ROLE_PARENT,
    ROLE_STUDENT,
    ROLE_TEACHER,
    decode_access_token,
    get_current_user,
)
from config import settings
from core.database import redis_client
from core.rate_limit import check_rate_limit
from core.session_manager import SessionManager
from repos.class_repo import teacher_can_access_student
from repos.knowledge_repo import get_doc_ids_for_learner
from repos.memory_repo import get_recent_memories, get_student_profile, save_learning_memory
from repos.parent_repo import is_parent_of
from repos.session_repo import (
    get_all_sessions,
    get_session_by_id,
    get_sessions_by_learner,
    get_turns_by_session,
    save_turn,
)
from repos.voice_repo import get_voice_for_learner
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


async def _can_access_learner(current: CurrentUser, learner_id: str) -> bool:
    if current.role == ROLE_ADMIN:
        return True
    if current.role == ROLE_STUDENT:
        return learner_id == current.email
    if current.role == ROLE_TEACHER:
        if learner_id == current.email:
            return True
        return await teacher_can_access_student(current.email, learner_id)
    if current.role == ROLE_PARENT:
        return await is_parent_of(current.email, learner_id)
    return False


@router.post("", response_model=SessionResponse)
async def create_session(
    payload: SessionCreateRequest,
    request: Request,
    current: CurrentUser = Depends(get_current_user),
) -> SessionResponse:
    await check_rate_limit(
        key=f"ratelimit:session-create:{current.email}:{request.client.host if request.client else 'unknown'}",
        limit=settings.session_create_rate_limit,
        window_seconds=settings.session_create_rate_window_seconds,
        detail="Too many session creation attempts. Please try again later.",
    )

    if session_mgr.active_count >= settings.max_concurrent_sessions:
        raise HTTPException(status_code=429, detail="Max concurrent sessions reached")

    requested_learner = (payload.learner_id or "").strip()
    if current.role == ROLE_STUDENT:
        learner_id = current.email
    elif current.role == ROLE_TEACHER:
        if not requested_learner or requested_learner == current.email:
            raise HTTPException(
                status_code=400,
                detail="Teachers must provide a student learner_id from their classes",
            )
        if not await teacher_can_access_student(current.email, requested_learner):
            raise HTTPException(
                status_code=403,
                detail="This learner is not in any of your classes",
            )
        learner_id = requested_learner
    elif current.role == ROLE_ADMIN:
        learner_id = requested_learner or current.email
    else:
        raise HTTPException(
            status_code=403,
            detail="Parents cannot start a learning session",
        )

    session = await session_mgr.create(learner_id, payload.lesson_topic)
    logger.info(
        "session_created",
        extra={"session_id": session.session_id, "user_email": current.email},
    )
    return session


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    learner_id: str | None = None,
    current: CurrentUser = Depends(get_current_user),
) -> SessionListResponse:
    if current.role == ROLE_STUDENT:
        target = current.email
    elif current.role == ROLE_PARENT:
        if learner_id is None or not await is_parent_of(current.email, learner_id):
            return SessionListResponse(sessions=[], total=0)
        target = learner_id
    elif current.role == ROLE_TEACHER:
        if learner_id is None:
            return SessionListResponse(sessions=[], total=0)
        if learner_id != current.email and not await teacher_can_access_student(
            current.email, learner_id
        ):
            raise HTTPException(status_code=403, detail="Learner is not in your classes")
        target = learner_id
    else:
        target = learner_id

    rows = await get_sessions_by_learner(target) if target else await get_all_sessions()
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


async def _ensure_session_access(session_id: str, current: CurrentUser) -> SessionResponse:
    active = session_mgr.get(session_id)
    if active is not None:
        learner_id = active.learner_id
        session = active
    else:
        row = await get_session_by_id(session_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Session not found")
        learner_id = str(row["learner_id"])
        session = SessionResponse(
            session_id=str(row["session_id"]),
            learner_id=learner_id,
            lesson_topic=str(row["lesson_topic"]),
            status=str(row["status"]),
            created_at=row["created_at"],
        )
    if not await _can_access_learner(current, learner_id):
        raise HTTPException(status_code=403, detail="Not allowed to access this session")
    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current: CurrentUser = Depends(get_current_user),
) -> SessionResponse:
    return await _ensure_session_access(session_id, current)


@router.get("/{session_id}/turns", response_model=list[TurnHistoryItem])
async def get_session_turns(
    session_id: str,
    current: CurrentUser = Depends(get_current_user),
) -> list[TurnHistoryItem]:
    await _ensure_session_access(session_id, current)
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
    current: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    session_resp = await _ensure_session_access(session_id, current)
    if current.role == ROLE_PARENT:
        raise HTTPException(status_code=403, detail="Parents cannot end a session")

    # Generate session summary for student memory
    learner_id = session_resp.learner_id
    lesson_topic = session_resp.lesson_topic
    try:
        turn_rows = await get_turns_by_session(session_id)
        if turn_rows:
            turns_for_summary = []
            for row in turn_rows:
                turns_for_summary.append({"role": "learner", "text": str(row["transcript"])})
                turns_for_summary.append({"role": "tutor", "text": str(row["assistant_response"])})

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{settings.llm_url}/summarize",
                        json={
                            "session_turns": turns_for_summary,
                            "lesson_topic": lesson_topic,
                        },
                    )
                    if resp.status_code == 200:
                        summary_data = resp.json()
                        await save_learning_memory(
                            student_email=learner_id,
                            session_id=session_id,
                            summary=summary_data.get("summary", ""),
                            topics_covered=summary_data.get("topics_covered", ""),
                            mistakes_made=summary_data.get("mistakes_made", ""),
                            mastery_score=float(summary_data.get("mastery_score", 0)),
                        )
            except Exception:
                logger.warning("session_summary_failed", extra={"session_id": session_id})
    except Exception:
        logger.warning("summary_turn_fetch_failed", extra={"session_id": session_id})

    try:
        await session_mgr.end(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    logger.info(
        "session_ended",
        extra={"session_id": session_id, "user_email": current.email},
    )
    return {"status": "ended", "session_id": session_id}


@router.post("/{session_id}/turns", response_model=TurnResponse)
async def process_turn(
    session_id: str,
    payload: TurnRequest,
    current: CurrentUser = Depends(get_current_user),
) -> TurnResponse:
    if not session_mgr.is_active(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    await _ensure_session_access(session_id, current)
    if current.role == ROLE_PARENT:
        raise HTTPException(status_code=403, detail="Parents cannot send turns")

    try:
        session = session_mgr.get(session_id)
        lesson_topic = session.lesson_topic if session else ""
        learner_id = session.learner_id if session else ""

        # Parallel lookups: history, doc_ids, student profile, memories, voice
        turns_task = get_turns_by_session(session_id)
        if learner_id:
            doc_ids_task = get_doc_ids_for_learner(learner_id)
            profile_task = get_student_profile(learner_id)
            memories_task = get_recent_memories(learner_id, limit=3)
            voice_task = get_voice_for_learner(learner_id)
            turn_rows, doc_ids, profile, memories, voice_info = await asyncio.gather(
                turns_task, doc_ids_task, profile_task, memories_task, voice_task,
            )
        else:
            turn_rows = await turns_task
            doc_ids: list[str] = []
            profile = None
            memories: list[dict[str, object]] = []
            voice_info = None

        history: list[dict[str, str]] = []
        for row in turn_rows[-10:]:
            history.append({"role": "learner", "text": str(row["transcript"])})
            history.append({"role": "tutor", "text": str(row["assistant_response"])})

        # RAG - retrieve knowledge chunks
        context_chunks: list[str] | None = None
        if doc_ids:
            query_text = payload.text_input or lesson_topic
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{settings.knowledge_url}/query",
                        json={"query": query_text, "doc_ids": doc_ids, "top_k": 5},
                    )
                    if resp.status_code == 200:
                        chunks_data = resp.json().get("chunks", [])
                        context_chunks = [c["text"] for c in chunks_data if c.get("score", 0) > 0.3]
            except Exception:
                logger.warning("knowledge_query_failed", extra={"session_id": session_id})

        # Student memory context
        student_context: dict[str, object] | None = None
        if profile or memories:
            student_context = {
                "learning_style": str(profile["learning_style"]) if profile else "balanced",
                "difficulty_level": str(profile["difficulty_level"]) if profile else "medium",
                "strengths": str(profile["strengths"]) if profile else "[]",
                "weaknesses": str(profile["weaknesses"]) if profile else "[]",
                "recent_summaries": [str(m["summary"]) for m in memories],
            }

        # Voice profile
        voice_id: str | None = None
        if voice_info and voice_info.get("external_voice_id"):
            voice_id = str(voice_info["external_voice_id"])

        result = await orchestrator.run_turn(
            text_input=payload.text_input,
            audio_base64=payload.audio_base64,
            lesson_topic=lesson_topic,
            history=history,
            context_chunks=context_chunks,
            student_context=student_context,
            voice_id=voice_id,
        )
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
            {"type": "turn_completed", "payload": response.model_dump(), "user_email": current.email},
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

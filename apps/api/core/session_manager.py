from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import WebSocket

from core.database import redis_client
from repos.session_repo import save_session, update_session_status
from schemas import SessionResponse

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self) -> None:
        self._active: dict[str, SessionResponse] = {}
        self._connections: dict[str, set[WebSocket]] = {}

    @property
    def active_sessions(self) -> dict[str, SessionResponse]:
        return self._active

    @property
    def active_count(self) -> int:
        return len(self._active)

    async def create(self, learner_id: str, lesson_topic: str) -> SessionResponse:
        session = SessionResponse(
            session_id=str(uuid4()),
            learner_id=learner_id,
            lesson_topic=lesson_topic,
            created_at=datetime.now(UTC),
            status="active",
        )
        self._active[session.session_id] = session
        self._connections[session.session_id] = set()
        await save_session(session.session_id, learner_id, lesson_topic, session.status)
        try:
            await redis_client.set(f"session:{session.session_id}:status", session.status, ex=3600)
        except Exception:
            logger.warning("redis_session_write_failed", extra={"session_id": session.session_id})
        return session

    def get(self, session_id: str) -> SessionResponse | None:
        return self._active.get(session_id)

    def is_active(self, session_id: str) -> bool:
        return session_id in self._active

    async def end(self, session_id: str) -> SessionResponse:
        session = self._active.pop(session_id, None)
        if session is None:
            raise KeyError(f"Session {session_id} not found")
        session.status = "ended"
        await update_session_status(session_id, "ended")
        await self.broadcast(session_id, {"type": "session_ended", "session_id": session_id})
        conns = self._connections.pop(session_id, set())
        for ws in conns:
            try:
                await ws.close()
            except Exception:
                pass
        try:
            await redis_client.delete(f"session:{session_id}:status")
        except Exception:
            pass
        return session

    def add_connection(self, session_id: str, ws: WebSocket) -> None:
        self._connections.setdefault(session_id, set()).add(ws)

    def remove_connection(self, session_id: str, ws: WebSocket) -> None:
        self._connections.get(session_id, set()).discard(ws)

    async def broadcast(self, session_id: str, event: dict[str, object]) -> None:
        sockets = self._connections.get(session_id, set())
        closed: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_json(event)
            except Exception:
                closed.append(ws)
        for ws in closed:
            sockets.discard(ws)

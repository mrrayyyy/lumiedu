"""Backward-compatible re-exports.

All database logic has moved into ``core.database`` (connection/schema management)
and ``repos.*`` (query functions).  This module re-exports everything so existing
``from db import ...`` statements in tests or Dockerfiles continue to work.
"""
from __future__ import annotations

from core.database import (
    close_connections,
    engine,
    ensure_db_ready,
    ping_dependencies,
    redis_client,
)
from repos.progress_repo import get_learner_progress
from repos.session_repo import (
    get_all_sessions,
    get_sessions_by_learner,
    get_turns_by_session,
    save_session,
    save_turn,
    update_session_status,
)
from repos.user_repo import get_user_credentials

__all__ = [
    "close_connections",
    "engine",
    "ensure_db_ready",
    "get_all_sessions",
    "get_learner_progress",
    "get_sessions_by_learner",
    "get_turns_by_session",
    "get_user_credentials",
    "ping_dependencies",
    "redis_client",
    "save_session",
    "save_turn",
    "update_session_status",
]

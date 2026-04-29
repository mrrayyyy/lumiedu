from __future__ import annotations

from fastapi import APIRouter, Depends

from auth import get_current_user_email
from config import settings
from core.database import ping_dependencies

router = APIRouter()

metrics: dict[str, int] = {"turn_total": 0, "turn_error_total": 0, "e2e_latency_ms_last": 0}


@router.get("/health")
async def health() -> dict[str, object]:
    deps = await ping_dependencies()
    return {"status": "ok", "environment": settings.app_env, "dependencies": deps}


@router.get("/api/health")
async def api_health() -> dict[str, object]:
    return await health()


@router.get("/metrics")
async def get_metrics(_: str = Depends(get_current_user_email)) -> dict[str, int]:
    return metrics


@router.get("/api/metrics")
async def api_metrics(_: str = Depends(get_current_user_email)) -> dict[str, int]:
    return metrics

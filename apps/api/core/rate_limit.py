from __future__ import annotations

import logging

from fastapi import HTTPException

from core.database import redis_client

logger = logging.getLogger(__name__)


async def check_rate_limit(key: str, limit: int, window_seconds: int, detail: str) -> None:
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

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from core.database import close_connections, ensure_db_ready
from routers import auth_router, health, progress, sessions

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("lumiedu-api")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await ensure_db_ready()
    logger.info("startup_complete")
    yield
    await sessions.orchestrator.close()
    await close_connections()
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    application = FastAPI(title=settings.app_name, lifespan=lifespan)

    allowed_origins = [o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router)
    application.include_router(auth_router.router)
    application.include_router(sessions.router)
    application.include_router(progress.router)

    return application


app = create_app()

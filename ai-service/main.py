"""
FixLoop AI — FastAPI AI Service
================================
Entry point.  Registers all routers, configures middleware,
and wires lifespan events (DB pool, OpenAI client).

Run locally:
    uvicorn main:app --reload --port 8000

Production:
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from api.cluster import router as cluster_router
from api.ingest import router as ingest_router
from api.investigate import router as investigate_router
from api.recommend import router as recommend_router
from api.validate import router as validate_router
from core.config import settings
from core.logging import configure_logging

logger = structlog.get_logger(__name__)


# ----------------------------------------------------------------
# Lifespan: startup / shutdown
# ----------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise shared resources on startup; clean up on shutdown."""
    configure_logging()
    logger.info(
        "fixloop_ai_service_starting",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )

    # Core services initialized via deps.py lazily or via connection pools
    pass

    yield

    logger.info("fixloop_ai_service_shutdown")
    # Clean up any persistent pools here


# ----------------------------------------------------------------
# Application factory
# ----------------------------------------------------------------
def create_app() -> FastAPI:
    app = FastAPI(
        title="FixLoop AI Service",
        description=(
            "AI pipeline for ticket ingestion, semantic clustering, "
            "root-cause investigation, fix recommendation, and validation."
        ),
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # ---- CORS ----
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Routers ----
    app.include_router(ingest_router,     prefix="/ai", tags=["Ingest"])
    app.include_router(cluster_router,    prefix="/ai", tags=["Cluster"])
    app.include_router(investigate_router, prefix="/ai", tags=["Investigate"])
    app.include_router(recommend_router,  prefix="/ai", tags=["Recommend"])
    app.include_router(validate_router,   prefix="/ai", tags=["Validate"])

    # ---- Health ----
    @app.get("/health", tags=["Health"], summary="Liveness probe")
    async def health() -> dict:
        return {"status": "ok", "version": settings.APP_VERSION}

    return app


app = create_app()

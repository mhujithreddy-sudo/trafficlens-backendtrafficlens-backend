"""
TrafficLens - Network Traffic Monitor
Main FastAPI application entrypoint with lifespan event management,
CORS configuration, centralized error handling, and router registration.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging_config import logger
from app.core.database import init_db
from app.services.bandwidth_monitor import bandwidth_monitor
from app.services.packet_analyzer import packet_analyzer
from app.services.device_discovery import device_discovery

# Route imports
from app.api.routes.health import router as health_router
from app.api.routes.network import router as network_router
from app.api.routes.bandwidth import router as bandwidth_router
from app.api.routes.devices import router as devices_router
from app.api.routes.services import router as services_router
from app.api.routes.traffic import router as traffic_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.history import router as history_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.settings import router as settings_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifecycle context manager for FastAPI:
    Initializes database and background services at startup;
    ensures clean shutdown when application terminates.
    """
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.APP_ENV}]...")

    # 1. Initialize database tables automatically
    try:
        init_db()
    except Exception as exc:
        logger.error(f"Critical error initializing database: {exc}")

    # 2. Start background telemetry monitors
    try:
        bandwidth_monitor.start()
    except Exception as exc:
        logger.error(f"Error starting bandwidth monitor: {exc}")

    try:
        packet_analyzer.start()
    except Exception as exc:
        logger.error(f"Error starting packet capture worker: {exc}")

    # 3. Initial device discovery pass
    try:
        device_discovery.discover_devices()
    except Exception as exc:
        logger.warning(f"Initial device discovery warning: {exc}")

    logger.info("TrafficLens background services successfully initialized.")

    yield

    # Clean shutdown
    logger.info("TrafficLens shutting down background monitoring workers...")
    try:
        packet_analyzer.stop()
    except Exception as exc:
        logger.error(f"Error stopping packet capture worker: {exc}")

    try:
        bandwidth_monitor.stop()
    except Exception as exc:
        logger.error(f"Error stopping bandwidth monitor: {exc}")

    logger.info("TrafficLens backend stopped cleanly.")


app = FastAPI(
    title="TrafficLens – Network Traffic Monitor API",
    description=(
        "Production-quality REST API backend for TrafficLens. "
        "Provides real-time bandwidth telemetry, network adapter accounting, "
        "device discovery, transport socket mapping, and packet flow analytics."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Centralized Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches unhandled errors, logs them internally, and returns safe JSON response."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=settings.DEBUG)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error occurred",
            "status_code": 500,
            "path": request.url.path,
        },
    )


# Root endpoint
@app.get("/", tags=["Root"])
def root():
    """Root endpoint welcoming clients and directing to OpenAPI documentation."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
        "status": "online",
    }


# Register all API routes under /api
api_prefix = "/api"
app.include_router(health_router, prefix=api_prefix)
app.include_router(network_router, prefix=api_prefix)
app.include_router(bandwidth_router, prefix=api_prefix)
app.include_router(devices_router, prefix=api_prefix)
app.include_router(services_router, prefix=api_prefix)
app.include_router(traffic_router, prefix=api_prefix)
app.include_router(analytics_router, prefix=api_prefix)
app.include_router(history_router, prefix=api_prefix)
app.include_router(alerts_router, prefix=api_prefix)
app.include_router(settings_router, prefix=api_prefix)

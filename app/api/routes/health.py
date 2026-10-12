"""
Health check endpoint.
Verifies service status, database connectivity, and monitoring availability.
"""

import time
from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.core.database import check_db_health
from app.services.bandwidth_monitor import bandwidth_monitor

router = APIRouter(prefix="/health", tags=["Health"])

START_TIME = time.time()


@router.get("", summary="System Health Check", description="Returns backend health, database connection, and monitoring availability.")
def get_health():
    """Verify backend components and database connectivity."""
    db_ok = check_db_health()
    uptime = round(time.time() - START_TIME, 2)

    return {
        "status": "online" if db_ok else "degraded",
        "service": "TrafficLens Backend",
        "version": settings.APP_VERSION,
        "database": "connected" if db_ok else "disconnected",
        "monitoring": "available" if bandwidth_monitor._running else "idle",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime,
    }

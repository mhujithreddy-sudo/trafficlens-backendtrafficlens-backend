"""
Bandwidth monitoring and history endpoints.
"""

from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.bandwidth import BandwidthCurrentResponse, BandwidthHistoryResponse
from app.services.bandwidth_monitor import bandwidth_monitor
from app.services.history_service import history_service

router = APIRouter(prefix="/bandwidth", tags=["Bandwidth"])


@router.get("", response_model=BandwidthCurrentResponse, summary="Get Instantaneous Bandwidth", description="Returns current transfer rates in bps and Mbps, byte counts, and traffic classification.")
def get_bandwidth():
    """Retrieve instantaneous bandwidth telemetry."""
    return bandwidth_monitor.get_current()


@router.get("/history", response_model=BandwidthHistoryResponse, summary="Get Bandwidth History", description="Returns historical bandwidth measurements filtered by hours or limit.")
def get_bandwidth_history(
    hours: Optional[int] = Query(None, description="Filter history to the last N hours", ge=1),
    limit: int = Query(60, description="Maximum number of historical records to retrieve", ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve historical bandwidth records."""
    records = history_service.get_bandwidth_history(db=db, hours=hours, limit=limit)
    return {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "records_count": len(records),
        "history": records,
    }

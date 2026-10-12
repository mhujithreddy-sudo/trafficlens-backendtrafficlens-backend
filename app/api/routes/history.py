"""
History querying endpoints for bandwidth, traffic, and devices.
"""

from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.services.history_service import history_service
from app.services.bandwidth_monitor import bandwidth_monitor

router = APIRouter(prefix="/history", tags=["History"])


@router.get("", summary="Get Rolling Bandwidth History (Frontend Compatible)", description="Returns rolling bandwidth history compatible with the Next.js frontend.")
def get_rolling_history(
    limit: int = Query(60, description="Number of rolling records to return", ge=1, le=500),
):
    """Retrieve rolling in-memory bandwidth history for live charts."""
    history_records = bandwidth_monitor.get_history(limit=limit)
    return {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "records_count": len(history_records),
        "history": history_records,
    }


@router.get("/bandwidth", summary="Get Bandwidth History", description="Queries historical bandwidth samples from the database with time filters.")
def get_bandwidth_history(
    hours: Optional[int] = Query(None, description="Hours of history to fetch", ge=1),
    limit: int = Query(100, description="Max records", ge=1, le=1000),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO 8601)"),
    db: Session = Depends(get_db),
):
    """Retrieve stored bandwidth records."""
    records = history_service.get_bandwidth_history(
        db=db, hours=hours, limit=limit, start_date=start_date, end_date=end_date
    )
    return {
        "status": "success",
        "records_count": len(records),
        "records": records,
    }


@router.get("/traffic", summary="Get Traffic Flow History", description="Queries historical packet and connection flow records.")
def get_traffic_history(
    limit: int = Query(100, description="Max records", ge=1, le=1000),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO 8601)"),
    db: Session = Depends(get_db),
):
    """Retrieve stored traffic flow records."""
    records = history_service.get_traffic_history(
        db=db, limit=limit, start_date=start_date, end_date=end_date
    )
    return {
        "status": "success",
        "records_count": len(records),
        "records": records,
    }


@router.get("/devices", summary="Get Device Discovery History", description="Queries historical device records.")
def get_device_history(
    limit: int = Query(100, description="Max records", ge=1, le=1000),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO 8601)"),
    db: Session = Depends(get_db),
):
    """Retrieve stored device discovery records."""
    records = history_service.get_devices_history(
        db=db, limit=limit, start_date=start_date, end_date=end_date
    )
    return {
        "status": "success",
        "records_count": len(records),
        "records": records,
    }

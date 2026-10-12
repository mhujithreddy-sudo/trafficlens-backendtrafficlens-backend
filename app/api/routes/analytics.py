"""
Analytics routes: dashboard overview, top consumers, and chart timelines.
"""

from typing import List
from fastapi import APIRouter, Query
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    TopDeviceItem,
    TopServiceItem,
    TimelineResponse,
)
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse, summary="Get Dashboard Overview", description="Returns high-level bandwidth telemetry, active device counts, and traffic levels.")
def get_analytics_overview():
    """Retrieve complete overview statistics for the main dashboard."""
    return analytics_service.get_overview()


@router.get("/top-devices", response_model=List[TopDeviceItem], summary="Get Top Devices by Traffic", description="Returns devices ranked deterministically by total data consumption.")
def get_top_devices(
    limit: int = Query(10, description="Number of top devices to return", ge=1, le=50)
):
    """Retrieve top traffic-heavy devices."""
    return analytics_service.get_top_devices(limit=limit)


@router.get("/top-services", response_model=List[TopServiceItem], summary="Get Top Services by Traffic", description="Returns network services ranked by observed traffic and bandwidth share.")
def get_top_services(
    limit: int = Query(10, description="Number of top services to return", ge=1, le=50)
):
    """Retrieve top traffic-heavy network services."""
    return analytics_service.get_top_services(limit=limit)


@router.get("/timeline", response_model=TimelineResponse, summary="Get Historical Timeline Data", description="Returns time-series data points for bandwidth chart plotting (1h, 6h, 24h, 7d).")
def get_timeline(
    range: str = Query("1h", description="Time range for chart series: 1h, 6h, 24h, 7d")
):
    """Retrieve time-series data points for frontend charts."""
    points = analytics_service.get_timeline(range_str=range)
    return {
        "status": "success",
        "range": range,
        "points_count": len(points),
        "points": points,
    }

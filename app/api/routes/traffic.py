"""
Traffic inspection and packet analytics endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Query
from app.schemas.traffic import TrafficListResponse, TrafficSummaryResponse
from app.services.packet_analyzer import packet_analyzer

router = APIRouter(prefix="/traffic", tags=["Traffic"])


@router.get("", response_model=TrafficListResponse, summary="Get Recent Traffic Flows", description="Returns recently observed network packet flows with filtering by protocol or IP.")
def get_traffic(
    limit: int = Query(50, description="Maximum number of records to return", ge=1, le=500),
    protocol: Optional[str] = Query(None, description="Filter by transport protocol (e.g. TCP, UDP)"),
    source_ip: Optional[str] = Query(None, description="Filter by source IP address"),
    destination_ip: Optional[str] = Query(None, description="Filter by destination IP address"),
):
    """Retrieve filtered recent packet / socket flow records."""
    records = packet_analyzer.get_recent_traffic(
        limit=limit,
        protocol=protocol,
        source_ip=source_ip,
        destination_ip=destination_ip,
    )
    return {
        "status": "success",
        "total_count": len(records),
        "records": records,
        "packet_capture_active": packet_analyzer.is_capture_available,
    }


@router.get("/summary", response_model=TrafficSummaryResponse, summary="Get Traffic Summary", description="Returns cumulative protocol distribution, byte totals, and top communicators.")
def get_traffic_summary():
    """Retrieve cumulative packet capture statistics and top talkers."""
    return packet_analyzer.get_summary()

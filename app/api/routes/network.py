"""
Network information and adapter telemetry route.
"""

from fastapi import APIRouter
from app.services.network_monitor import network_monitor

router = APIRouter(prefix="/network", tags=["Network"])


@router.get("", summary="Get Network Topology & Telemetry", description="Returns host networking details, active network adapters, and cumulative I/O statistics.")
def get_network_info():
    """Retrieve host network interfaces, local IP, gateway, and byte counters."""
    return network_monitor.get_network_overview()

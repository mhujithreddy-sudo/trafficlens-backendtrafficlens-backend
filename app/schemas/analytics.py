"""
Pydantic models for analytics: overview, top-devices, top-services, timeline.
"""

from typing import List, Optional
from pydantic import BaseModel


class AnalyticsOverviewResponse(BaseModel):
    total_bandwidth: int
    total_bandwidth_formatted: str
    download_bytes: int
    download_bytes_formatted: str
    upload_bytes: int
    upload_bytes_formatted: str
    active_devices: int
    total_packets: int
    current_download_mbps: float
    current_upload_mbps: float
    current_download_rate: str
    current_upload_rate: str
    peak_download_mbps: float
    peak_upload_mbps: float
    traffic_level: str  # LOW, MEDIUM, HIGH
    network_load: str   # Normal, Moderate, Heavy


class TopDeviceItem(BaseModel):
    device: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    download_bytes: int
    upload_bytes: int
    total_bytes: int
    total_bytes_formatted: str
    percentage: float


class TopServiceItem(BaseModel):
    service: str
    protocol: str
    download_bytes: int
    upload_bytes: int
    total_bytes: int
    total_bytes_formatted: str
    percentage: float


class TimelinePoint(BaseModel):
    timestamp: str
    time: str
    download_mbps: float
    upload_mbps: float
    total_mbps: float
    download_bytes: int
    upload_bytes: int


class TimelineResponse(BaseModel):
    status: str = "success"
    range: str
    points_count: int
    points: List[TimelinePoint]

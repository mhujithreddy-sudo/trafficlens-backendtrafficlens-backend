"""
Pydantic models for bandwidth monitoring.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BandwidthCurrentResponse(BaseModel):
    timestamp: str
    active_interface: str
    total_bytes_sent: int
    total_bytes_recv: int
    upload_speed_bps: float
    download_speed_bps: float
    upload_mbps: float
    download_mbps: float
    total_mbps: float
    upload_speed_formatted: str
    download_speed_formatted: str
    total_speed_formatted: str
    download_bytes_formatted: str
    upload_bytes_formatted: str
    total_bytes_formatted: str
    packets_sent: int = 0
    packets_recv: int = 0
    traffic_level: str = "LOW"  # LOW, MEDIUM, HIGH


class BandwidthHistoryItem(BaseModel):
    id: Optional[int] = None
    timestamp: str
    time: str
    interface_name: str = "all"
    download_bytes: int = 0
    upload_bytes: int = 0
    download_mbps: float = 0.0
    upload_mbps: float = 0.0
    download: float = 0.0  # In KB/s or bps for backwards compatibility
    upload: float = 0.0
    total: float = 0.0
    download_formatted: str = "0.00 B/s"
    upload_formatted: str = "0.00 B/s"
    total_formatted: str = "0.00 B/s"

    model_config = ConfigDict(from_attributes=True)


class BandwidthHistoryResponse(BaseModel):
    status: str = "success"
    timestamp: str
    records_count: int
    history: List[BandwidthHistoryItem]

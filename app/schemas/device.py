"""
Pydantic models for network devices and interfaces.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DeviceBase(BaseModel):
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    device_type: str = "unknown"
    status: str = "online"


class DeviceItem(DeviceBase):
    id: Optional[int] = None
    device_name: str
    interface: Optional[str] = None
    download_usage: int = 0
    upload_usage: int = 0
    total_usage: int = 0
    download_bytes: int = 0
    upload_bytes: int = 0
    download_usage_formatted: str = "0.00 B"
    upload_usage_formatted: str = "0.00 B"
    total_usage_formatted: str = "0.00 B"
    speed_mbps: Optional[float] = None
    is_local: bool = False
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DevicesResponse(BaseModel):
    status: str = "success"
    timestamp: str
    devices_count: int
    devices: List[DeviceItem]
    limitation_note: Optional[str] = None


class DeviceDetailResponse(BaseModel):
    device: DeviceItem
    recent_traffic: List[dict] = []
    top_services: List[dict] = []

"""
Pydantic models for settings and alerts.
"""

from typing import List, Optional
from pydantic import BaseModel


class SettingsResponse(BaseModel):
    app_name: str
    app_env: str
    monitoring_mode: str
    packet_capture_enabled: bool
    packet_capture_available: bool
    sample_interval_seconds: float
    history_retention_hours: int
    traffic_level_low_mbps: float
    traffic_level_medium_mbps: float
    bandwidth_alert_threshold_mbps: float
    cors_origins: List[str]


class SettingsUpdateRequest(BaseModel):
    monitoring_mode: Optional[str] = None
    packet_capture_enabled: Optional[bool] = None
    sample_interval_seconds: Optional[float] = None
    history_retention_hours: Optional[int] = None
    traffic_level_low_mbps: Optional[float] = None
    traffic_level_medium_mbps: Optional[float] = None
    bandwidth_alert_threshold_mbps: Optional[float] = None


class AlertItem(BaseModel):
    id: Optional[int] = None
    timestamp: str
    type: str  # e.g., traffic_spike, bandwidth_spike
    severity: str  # info, warning, critical
    message: str
    device_id: Optional[int] = None
    resolved: bool = False


class AlertsResponse(BaseModel):
    status: str = "success"
    alerts_count: int
    alerts: List[AlertItem]

"""
Settings management endpoints.
"""

from fastapi import APIRouter
from app.core.config import settings
from app.schemas.settings import SettingsResponse, SettingsUpdateRequest
from app.services.packet_analyzer import packet_analyzer

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsResponse, summary="Get Current Settings", description="Returns runtime monitoring configuration and thresholds.")
def get_settings():
    """Retrieve current system configuration and monitoring thresholds."""
    return SettingsResponse(
        app_name=settings.APP_NAME,
        app_env=settings.APP_ENV,
        monitoring_mode=settings.MONITORING_MODE,
        packet_capture_enabled=settings.PACKET_CAPTURE_ENABLED,
        packet_capture_available=packet_analyzer.is_capture_available,
        sample_interval_seconds=settings.SAMPLE_INTERVAL_SECONDS,
        history_retention_hours=settings.HISTORY_RETENTION_HOURS,
        traffic_level_low_mbps=settings.TRAFFIC_LEVEL_LOW_MBPS,
        traffic_level_medium_mbps=settings.TRAFFIC_LEVEL_MEDIUM_MBPS,
        bandwidth_alert_threshold_mbps=settings.BANDWIDTH_ALERT_THRESHOLD_MBPS,
        cors_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    )


@router.put("", response_model=SettingsResponse, summary="Update Settings", description="Dynamically update monitoring preferences and alert thresholds.")
def update_settings(update_data: SettingsUpdateRequest):
    """Update runtime monitoring configuration."""
    if update_data.monitoring_mode is not None:
        settings.MONITORING_MODE = update_data.monitoring_mode
    if update_data.packet_capture_enabled is not None:
        settings.PACKET_CAPTURE_ENABLED = update_data.packet_capture_enabled
    if update_data.sample_interval_seconds is not None:
        settings.SAMPLE_INTERVAL_SECONDS = update_data.sample_interval_seconds
    if update_data.history_retention_hours is not None:
        settings.HISTORY_RETENTION_HOURS = update_data.history_retention_hours
    if update_data.traffic_level_low_mbps is not None:
        settings.TRAFFIC_LEVEL_LOW_MBPS = update_data.traffic_level_low_mbps
    if update_data.traffic_level_medium_mbps is not None:
        settings.TRAFFIC_LEVEL_MEDIUM_MBPS = update_data.traffic_level_medium_mbps
    if update_data.bandwidth_alert_threshold_mbps is not None:
        settings.BANDWIDTH_ALERT_THRESHOLD_MBPS = update_data.bandwidth_alert_threshold_mbps

    return get_settings()

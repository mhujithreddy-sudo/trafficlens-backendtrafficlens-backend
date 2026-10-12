"""
Application configuration management using pydantic-settings.
Loads configuration from environment variables or .env file.
"""

from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for TrafficLens Backend."""

    APP_NAME: str = "TrafficLens"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = "sqlite:///./trafficlens.db"

    # CORS origins: can be specified as a comma-separated string or list in .env
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Monitoring Settings
    MONITORING_MODE: str = "real"  # "real" or "demo"
    PACKET_CAPTURE_ENABLED: bool = True
    SAMPLE_INTERVAL_SECONDS: float = 1.0
    HISTORY_MAX_IN_MEMORY: int = 120
    HISTORY_RETENTION_HOURS: int = 24
    DEVICE_DISCOVERY_INTERVAL_SECONDS: int = 30

    # Deterministic Traffic Level Thresholds (in Mbps)
    TRAFFIC_LEVEL_LOW_MBPS: float = 5.0
    TRAFFIC_LEVEL_MEDIUM_MBPS: float = 25.0

    # Anomaly / Alert Thresholds
    BANDWIDTH_ALERT_THRESHOLD_MBPS: float = 50.0
    TRAFFIC_SPIKE_FACTOR: float = 3.0  # Alert if rate is 3x higher than 30s rolling avg

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            # Split comma-separated string and strip whitespace
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_demo(self) -> bool:
        return self.MONITORING_MODE.lower() == "demo"


settings = Settings()

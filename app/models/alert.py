"""
SQLAlchemy model for network security and anomaly alerts.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
    alert_type = Column(String(50), nullable=False, index=True)  # traffic_spike, bandwidth_spike, high_device_usage
    severity = Column(String(20), default="warning", nullable=False)  # info, warning, critical
    message = Column(String(500), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    resolved = Column(Boolean, default=False, nullable=False)

    # Relationships
    device = relationship("Device", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert(type={self.alert_type}, sev={self.severity}, msg={self.message[:30]})>"

"""
SQLAlchemy model for network devices and interfaces.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, BigInteger, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hostname = Column(String(255), nullable=True)
    ip_address = Column(String(64), nullable=True, index=True)
    mac_address = Column(String(64), nullable=True, index=True)
    device_type = Column(String(50), default="unknown")  # 'interface', 'lan_neighbor', 'unknown'
    status = Column(String(20), default="online")        # 'online', 'offline'
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    download_bytes = Column(BigInteger, default=0, nullable=False)
    upload_bytes = Column(BigInteger, default=0, nullable=False)

    # Relationships
    traffic_records = relationship("TrafficRecord", back_populates="device", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="device", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Device(id={self.id}, ip={self.ip_address}, hostname={self.hostname})>"

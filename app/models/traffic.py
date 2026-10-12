"""
SQLAlchemy model for captured or observed network traffic records.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class TrafficRecord(Base):
    __tablename__ = "traffic_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
    source_ip = Column(String(64), nullable=False, index=True)
    destination_ip = Column(String(64), nullable=False, index=True)
    source_port = Column(Integer, nullable=True)
    destination_port = Column(Integer, nullable=True)
    protocol = Column(String(20), nullable=False, index=True)  # TCP, UDP, ICMP, etc.
    packet_count = Column(Integer, default=1, nullable=False)
    bytes = Column(BigInteger, default=0, nullable=False)
    download_bytes = Column(BigInteger, default=0, nullable=False)
    upload_bytes = Column(BigInteger, default=0, nullable=False)
    service = Column(String(64), default="Unknown", nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    device = relationship("Device", back_populates="traffic_records")

    def __repr__(self) -> str:
        return f"<TrafficRecord(src={self.source_ip}:{self.source_port}, dst={self.destination_ip}:{self.destination_port}, proto={self.protocol}, bytes={self.bytes})>"

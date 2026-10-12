"""
SQLAlchemy model for periodic bandwidth samples.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, BigInteger, Float, DateTime
from app.core.database import Base


class BandwidthRecord(Base):
    __tablename__ = "bandwidth_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
    interface_name = Column(String(100), default="all", nullable=False, index=True)
    download_bytes = Column(BigInteger, default=0, nullable=False)
    upload_bytes = Column(BigInteger, default=0, nullable=False)
    download_mbps = Column(Float, default=0.0, nullable=False)
    upload_mbps = Column(Float, default=0.0, nullable=False)

    def __repr__(self) -> str:
        return f"<BandwidthRecord(interface={self.interface_name}, down_mbps={self.download_mbps:.3f}, up_mbps={self.upload_mbps:.3f})>"

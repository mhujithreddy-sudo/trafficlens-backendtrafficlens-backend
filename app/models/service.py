"""
SQLAlchemy model for aggregated network services.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, BigInteger, DateTime
from app.core.database import Base


class ServiceRecord(Base):
    __tablename__ = "service_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
    service_name = Column(String(100), nullable=False, index=True)
    protocol = Column(String(20), nullable=False)
    port = Column(Integer, nullable=True)
    download_bytes = Column(BigInteger, default=0, nullable=False)
    upload_bytes = Column(BigInteger, default=0, nullable=False)
    total_bytes = Column(BigInteger, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<ServiceRecord(name={self.service_name}, proto={self.protocol}, total={self.total_bytes})>"

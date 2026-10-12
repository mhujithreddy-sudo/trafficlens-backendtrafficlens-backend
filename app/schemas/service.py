"""
Pydantic models for services and socket connection inspection.
"""

from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict


class ServiceItem(BaseModel):
    service: str
    protocol: str
    connection_count: int
    status: str = "ACTIVE"
    local_address: str
    remote_address: str
    sample_remote: Optional[str] = None
    download_bytes: int = 0
    upload_bytes: int = 0
    total_bytes: int = 0
    total_bytes_formatted: str = "0.00 B"


class ConnectionDetail(BaseModel):
    service: str
    pid: Optional[Union[int, str]] = None
    protocol: str
    local_address: str
    remote_address: str
    status: str


class ServicesResponse(BaseModel):
    status: str = "success"
    timestamp: str
    total_connections: int
    services: List[ServiceItem]
    connections: List[ConnectionDetail] = []

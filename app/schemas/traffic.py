"""
Pydantic models for packet traffic analysis and summary.
"""

from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TrafficRecordItem(BaseModel):
    id: Optional[int] = None
    timestamp: str
    source_ip: str
    destination_ip: str
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    protocol: str
    packet_count: int = 1
    bytes: int = 0
    bytes_formatted: str = "0.00 B"
    download_bytes: int = 0
    upload_bytes: int = 0
    service: str = "Unknown"
    device_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class TrafficListResponse(BaseModel):
    status: str = "success"
    total_count: int
    records: List[TrafficRecordItem]
    packet_capture_active: bool


class TopEntity(BaseModel):
    entity: Any
    count: int
    bytes: int
    bytes_formatted: str


class TrafficSummaryResponse(BaseModel):
    status: str = "success"
    timestamp: str
    total_packets: int
    total_bytes: int
    total_bytes_formatted: str
    tcp_packets: int
    udp_packets: int
    icmp_packets: int
    other_packets: int
    top_source_ips: List[TopEntity]
    top_destination_ips: List[TopEntity]
    top_ports: List[TopEntity]
    packet_capture_available: bool

"""
Device discovery and inspection endpoints.
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.device import DevicesResponse, DeviceDetailResponse
from app.services.device_discovery import device_discovery
from app.models.device import Device
from app.models.traffic import TrafficRecord
from app.utils.network_utils import format_bytes

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("", response_model=DevicesResponse, summary="Discover Network Devices", description="Returns discovered host network adapters and local LAN neighbors.")
def get_devices():
    """List detected local interfaces and observable LAN devices."""
    devices = device_discovery.discover_devices()
    return {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "devices_count": len(devices),
        "devices": devices,
        "limitation_note": device_discovery._limitation_note,
    }


@router.get("/{device_id}", response_model=DeviceDetailResponse, summary="Get Device Details", description="Returns detailed telemetry, byte accounting, and recent traffic for a specific device.")
def get_device(device_id: int):
    """Retrieve details, usage totals, and recent traffic for a specific device ID."""
    detail = device_discovery.get_device_by_id(device_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Device not found")
    return detail


@router.get("/{device_id}/traffic", summary="Get Device Traffic", description="Returns recent traffic flows associated with the given device.")
def get_device_traffic(
    device_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve recent traffic records associated with a specific device."""
    dev = db.query(Device).filter(Device.id == device_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found")

    traffic = (
        db.query(TrafficRecord)
        .filter((TrafficRecord.source_ip == dev.ip_address) | (TrafficRecord.destination_ip == dev.ip_address))
        .order_by(TrafficRecord.timestamp.desc())
        .limit(limit)
        .all()
    )

    return {
        "status": "success",
        "device_id": device_id,
        "device_name": dev.hostname or dev.ip_address,
        "traffic_count": len(traffic),
        "records": [
            {
                "id": t.id,
                "timestamp": t.timestamp.isoformat(),
                "source_ip": t.source_ip,
                "destination_ip": t.destination_ip,
                "source_port": t.source_port,
                "destination_port": t.destination_port,
                "protocol": t.protocol,
                "bytes": t.bytes,
                "bytes_formatted": format_bytes(t.bytes),
                "service": t.service,
            }
            for t in traffic
        ],
    }

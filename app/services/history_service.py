"""
Historical querying service for TrafficLens.
Queries database for traffic, bandwidth, and device records with date and limit filters.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.bandwidth import BandwidthRecord
from app.models.traffic import TrafficRecord
from app.models.device import Device
from app.services.bandwidth_monitor import bandwidth_monitor
from app.utils.network_utils import format_bytes, format_speed


class HistoryService:
    """Provides querying capabilities for stored network telemetry history."""

    def get_bandwidth_history(
        self,
        db: Session,
        hours: Optional[int] = None,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve historical bandwidth samples."""
        query = db.query(BandwidthRecord)

        if hours:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            query = query.filter(BandwidthRecord.timestamp >= cutoff)
        if start_date:
            query = query.filter(BandwidthRecord.timestamp >= start_date)
        if end_date:
            query = query.filter(BandwidthRecord.timestamp <= end_date)

        records = query.order_by(BandwidthRecord.timestamp.desc()).limit(limit).all()

        if not records:
            # Fallback to in-memory history if DB is empty / new run
            in_mem = bandwidth_monitor.get_history(limit=limit)
            return list(reversed(in_mem))

        results = []
        for r in records:
            down_bps = (r.download_mbps * 1_000_000.0) / 8.0
            up_bps = (r.upload_mbps * 1_000_000.0) / 8.0
            results.append({
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "time": r.timestamp.strftime("%H:%M:%S"),
                "interface_name": r.interface_name,
                "download_bytes": r.download_bytes,
                "upload_bytes": r.upload_bytes,
                "download_mbps": r.download_mbps,
                "upload_mbps": r.upload_mbps,
                "download": round(down_bps, 2),
                "upload": round(up_bps, 2),
                "total": round(down_bps + up_bps, 2),
                "download_formatted": format_speed(down_bps),
                "upload_formatted": format_speed(up_bps),
                "total_formatted": format_speed(down_bps + up_bps),
            })
        return results

    def get_traffic_history(
        self,
        db: Session,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve historical traffic records."""
        query = db.query(TrafficRecord)

        if start_date:
            query = query.filter(TrafficRecord.timestamp >= start_date)
        if end_date:
            query = query.filter(TrafficRecord.timestamp <= end_date)

        records = query.order_by(TrafficRecord.timestamp.desc()).limit(limit).all()

        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "source_ip": r.source_ip,
                "destination_ip": r.destination_ip,
                "source_port": r.source_port,
                "destination_port": r.destination_port,
                "protocol": r.protocol,
                "packet_count": r.packet_count,
                "bytes": r.bytes,
                "bytes_formatted": format_bytes(r.bytes),
                "download_bytes": r.download_bytes,
                "upload_bytes": r.upload_bytes,
                "service": r.service,
            }
            for r in records
        ]

    def get_devices_history(
        self,
        db: Session,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve historical device records."""
        query = db.query(Device)

        if start_date:
            query = query.filter(Device.last_seen >= start_date)
        if end_date:
            query = query.filter(Device.last_seen <= end_date)

        devices = query.order_by(Device.last_seen.desc()).limit(limit).all()

        return [
            {
                "id": d.id,
                "hostname": d.hostname,
                "ip_address": d.ip_address,
                "mac_address": d.mac_address,
                "device_type": d.device_type,
                "status": d.status,
                "download_bytes": d.download_bytes,
                "upload_bytes": d.upload_bytes,
                "total_bytes": d.download_bytes + d.upload_bytes,
                "total_bytes_formatted": format_bytes(d.download_bytes + d.upload_bytes),
                "first_seen": d.first_seen.isoformat() if d.first_seen else None,
                "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            }
            for d in devices
        ]


history_service = HistoryService()

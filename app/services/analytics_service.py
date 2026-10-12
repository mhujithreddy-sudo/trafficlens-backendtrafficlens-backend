"""
Analytics service.
Computes dashboard overview metrics, ranks top devices and services,
and generates historical timeline series for charts.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import psutil

from app.core.database import SessionLocal
from app.models.device import Device
from app.models.traffic import TrafficRecord
from app.models.bandwidth import BandwidthRecord
from app.services.bandwidth_monitor import bandwidth_monitor
from app.services.packet_analyzer import packet_analyzer
from app.utils.network_utils import format_bytes, format_speed


class AnalyticsService:
    """Computes network analytics, top consumer rankings, and time-series rollups."""

    def get_overview(self) -> Dict[str, Any]:
        """Aggregate high-level telemetry required by the TrafficLens dashboard."""
        io = psutil.net_io_counters()
        total_down = io.bytes_recv
        total_up = io.bytes_sent
        total_bw = total_down + total_up

        curr = bandwidth_monitor.get_current()
        curr_down_mbps = curr.get("download_mbps", 0.0)
        curr_up_mbps = curr.get("upload_mbps", 0.0)
        traffic_level = curr.get("traffic_level", "LOW")

        # Network load categorization
        if traffic_level == "HIGH":
            network_load = "Heavy"
        elif traffic_level == "MEDIUM":
            network_load = "Moderate"
        else:
            network_load = "Normal"

        # Count active devices from database or interfaces
        active_devices_count = 1
        try:
            with SessionLocal() as db:
                active_devices_count = db.query(Device).filter(Device.status == "online").count() or 1
        except Exception:
            pass

        return {
            "total_bandwidth": total_bw,
            "total_bandwidth_formatted": format_bytes(total_bw),
            "download_bytes": total_down,
            "download_bytes_formatted": format_bytes(total_down),
            "upload_bytes": total_up,
            "upload_bytes_formatted": format_bytes(total_up),
            "active_devices": active_devices_count,
            "total_packets": io.packets_recv + io.packets_sent,
            "current_download_mbps": curr_down_mbps,
            "current_upload_mbps": curr_up_mbps,
            "current_download_rate": format_speed(curr.get("download_speed_bps", 0.0)),
            "current_upload_rate": format_speed(curr.get("upload_speed_bps", 0.0)),
            "peak_download_mbps": bandwidth_monitor.peak_download_mbps,
            "peak_upload_mbps": bandwidth_monitor.peak_upload_mbps,
            "traffic_level": traffic_level,
            "network_load": network_load,
        }

    def get_top_devices(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return devices ranked by total traffic consumed."""
        try:
            with SessionLocal() as db:
                devices = db.query(Device).all()
                if not devices:
                    return []

                # Compute total sum for percentage calculation
                total_all_bytes = sum((d.download_bytes + d.upload_bytes) for d in devices)

                result = []
                for d in devices:
                    total_usage = d.download_bytes + d.upload_bytes
                    pct = round((total_usage / total_all_bytes) * 100.0, 1) if total_all_bytes > 0 else 0.0
                    result.append({
                        "device": d.hostname or f"Device-{d.id}",
                        "ip_address": d.ip_address,
                        "mac_address": d.mac_address,
                        "download_bytes": d.download_bytes,
                        "upload_bytes": d.upload_bytes,
                        "total_bytes": total_usage,
                        "total_bytes_formatted": format_bytes(total_usage),
                        "percentage": pct,
                    })

                # Sort by total_bytes descending
                result.sort(key=lambda x: x["total_bytes"], reverse=True)
                return result[:limit]
        except Exception:
            return []

    def get_top_services(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return services ranked by observed traffic."""
        try:
            with SessionLocal() as db:
                from sqlalchemy import func
                rows = (
                    db.query(
                        TrafficRecord.service,
                        TrafficRecord.protocol,
                        func.sum(TrafficRecord.download_bytes).label("down_bytes"),
                        func.sum(TrafficRecord.upload_bytes).label("up_bytes"),
                        func.sum(TrafficRecord.bytes).label("tot_bytes"),
                    )
                    .group_by(TrafficRecord.service, TrafficRecord.protocol)
                    .order_by(func.sum(TrafficRecord.bytes).desc())
                    .limit(limit)
                    .all()
                )

                if not rows:
                    # Fallback to in-memory packet analyzer counts if DB is fresh
                    recent = packet_analyzer.get_recent_traffic(limit=100)
                    service_sums = {}
                    for r in recent:
                        s = r.get("service", "Unknown")
                        proto = r.get("protocol", "TCP")
                        key = (s, proto)
                        if key not in service_sums:
                            service_sums[key] = {"down": 0, "up": 0, "tot": 0}
                        service_sums[key]["down"] += r.get("download_bytes", 0)
                        service_sums[key]["up"] += r.get("upload_bytes", 0)
                        service_sums[key]["tot"] += r.get("bytes", 0)

                    grand_total = sum(v["tot"] for v in service_sums.values())
                    fallback_result = []
                    for (srv, proto), v in service_sums.items():
                        pct = round((v["tot"] / grand_total) * 100.0, 1) if grand_total > 0 else 0.0
                        fallback_result.append({
                            "service": srv,
                            "protocol": proto,
                            "download_bytes": v["down"],
                            "upload_bytes": v["up"],
                            "total_bytes": v["tot"],
                            "total_bytes_formatted": format_bytes(v["tot"]),
                            "percentage": pct,
                        })
                    fallback_result.sort(key=lambda x: x["total_bytes"], reverse=True)
                    return fallback_result[:limit]

                grand_total = sum(r.tot_bytes for r in rows) or 1
                result = []
                for r in rows:
                    pct = round((r.tot_bytes / grand_total) * 100.0, 1)
                    result.append({
                        "service": r.service,
                        "protocol": r.protocol,
                        "download_bytes": r.down_bytes or 0,
                        "upload_bytes": r.up_bytes or 0,
                        "total_bytes": r.tot_bytes or 0,
                        "total_bytes_formatted": format_bytes(r.tot_bytes or 0),
                        "percentage": pct,
                    })
                return result
        except Exception:
            return []

    def get_timeline(self, range_str: str = "1h") -> List[Dict[str, Any]]:
        """Generate timeline data points for chart rendering."""
        range_map = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
        }
        delta = range_map.get(range_str, timedelta(hours=1))
        since_time = datetime.now(timezone.utc) - delta

        try:
            with SessionLocal() as db:
                records = (
                    db.query(BandwidthRecord)
                    .filter(BandwidthRecord.timestamp >= since_time)
                    .order_by(BandwidthRecord.timestamp.asc())
                    .limit(200)
                    .all()
                )

                if records:
                    return [
                        {
                            "timestamp": r.timestamp.isoformat(),
                            "time": r.timestamp.strftime("%H:%M:%S"),
                            "download_mbps": r.download_mbps,
                            "upload_mbps": r.upload_mbps,
                            "total_mbps": round(r.download_mbps + r.upload_mbps, 4),
                            "download_bytes": r.download_bytes,
                            "upload_bytes": r.upload_bytes,
                        }
                        for r in records
                    ]
        except Exception:
            pass

        # If no DB records yet, use in-memory rolling history
        in_memory = bandwidth_monitor.get_history(limit=60)
        return [
            {
                "timestamp": h["timestamp"],
                "time": h["time"],
                "download_mbps": h["download_mbps"],
                "upload_mbps": h["upload_mbps"],
                "total_mbps": h["total_mbps"],
                "download_bytes": int(h["upload_speed_bps"]),
                "upload_bytes": int(h["download_speed_bps"]),
            }
            for h in in_memory
        ]


analytics_service = AnalyticsService()

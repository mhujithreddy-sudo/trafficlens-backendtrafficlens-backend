"""
Service and protocol analyzer service.
Inspects active TCP/UDP sockets, associates them with local processes and standard ports,
and aggregates traffic per service.
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import socket
import psutil

from app.core.logging_config import logger
from app.utils.protocol_utils import identify_service
from app.utils.network_utils import format_bytes


class ServiceAnalyzerService:
    """Analyzes system transport connections and aggregates by protocol/service."""

    def __init__(self):
        self._proc_name_cache: Dict[int, str] = {}

    def _get_process_name(self, pid: Optional[int]) -> str:
        """Resolve process name by PID safely with caching."""
        if not pid:
            return "System / Unknown"
        if pid in self._proc_name_cache:
            return self._proc_name_cache[pid]
        try:
            p = psutil.Process(pid)
            name = p.name()
            self._proc_name_cache[pid] = name
            return name
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "System / Restricted"
        except Exception:
            return f"PID {pid}"

    def analyze_services(self) -> Dict[str, Any]:
        """
        Inspect current active network connections on host.
        Returns aggregated service metrics and detailed connection records.
        """
        services_map = defaultdict(lambda: {
            "service": "",
            "protocol": "TCP",
            "connection_count": 0,
            "status": "ESTABLISHED",
            "local_address": "",
            "remote_endpoints": set(),
            "download_bytes": 0,
            "upload_bytes": 0,
            "total_bytes": 0,
        })

        connections_list: List[Dict[str, Any]] = []

        try:
            conns = psutil.net_connections(kind="inet")
        except Exception as exc:
            logger.warning(f"Could not retrieve net_connections: {exc}")
            conns = []

        for conn in conns:
            proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
            laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "0.0.0.0:0"
            raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "*:*"
            status = conn.status if conn.status else "OPEN"

            proc_name = self._get_process_name(conn.pid)
            dest_port = conn.raddr.port if conn.raddr else None
            src_port = conn.laddr.port if conn.laddr else None

            # Standard service classification
            service_name = identify_service(src_port, dest_port, proto)

            # Combined grouping key: process and identified service
            group_key = f"{proc_name} ({service_name})" if proc_name != "System / Unknown" else service_name

            entry = services_map[group_key]
            entry["service"] = group_key
            entry["protocol"] = proto
            entry["connection_count"] += 1
            entry["local_address"] = laddr
            if conn.raddr:
                entry["remote_endpoints"].add(conn.raddr.ip)

            connections_list.append({
                "service": group_key,
                "pid": conn.pid or "N/A",
                "protocol": proto,
                "local_address": laddr,
                "remote_address": raddr,
                "status": status,
            })

        # Format services list
        formatted_services = []
        for key, s in services_map.items():
            remotes = list(s["remote_endpoints"])
            sample_remote = remotes[0] if remotes else "Localhost"
            remote_summary = f"{len(remotes)} endpoints" if len(remotes) > 1 else sample_remote

            formatted_services.append({
                "service": s["service"],
                "protocol": s["protocol"],
                "connection_count": s["connection_count"],
                "status": "ACTIVE",
                "local_address": s["local_address"],
                "remote_address": remote_summary,
                "sample_remote": sample_remote,
                "download_bytes": s["download_bytes"],
                "upload_bytes": s["upload_bytes"],
                "total_bytes": s["total_bytes"],
                "total_bytes_formatted": format_bytes(s["total_bytes"]),
            })

        # Sort services by connection count descending
        formatted_services.sort(key=lambda x: x["connection_count"], reverse=True)

        return {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_connections": len(conns),
            "services": formatted_services,
            "connections": connections_list[:100],  # Return up to top 100 connections
        }


service_analyzer = ServiceAnalyzerService()

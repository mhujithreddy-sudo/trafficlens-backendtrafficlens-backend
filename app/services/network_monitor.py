"""
Network information monitoring service.
Gathers hardware adapter status, IP/MAC configurations, and system network telemetry.
"""

import socket
from datetime import datetime, timezone
from typing import Dict, Any, List
import psutil

from app.utils.system_utils import get_os_info, get_local_ip, get_default_gateway
from app.utils.network_utils import format_bytes, format_speed, normalize_mac
from app.services.bandwidth_monitor import bandwidth_monitor


class NetworkMonitor:
    """Service providing host network topology, adapter telemetry, and interface statistics."""

    def get_network_overview(self) -> Dict[str, Any]:
        """Collect network overview telemetry."""
        hostname = socket.gethostname()
        local_ip = get_local_ip()
        gateway = get_default_gateway()
        os_info = get_os_info()

        # Interface details
        interfaces = self.get_interfaces()

        # Cumulative totals from psutil
        io = psutil.net_io_counters()
        total_recv = io.bytes_recv
        total_sent = io.bytes_sent
        total_bytes = total_recv + total_sent

        # Current speeds from bandwidth monitor
        bw = bandwidth_monitor.get_current()
        down_speed = bw.get("download_speed_bps", 0.0)
        up_speed = bw.get("upload_speed_bps", 0.0)
        tot_speed = down_speed + up_speed

        return {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hostname": hostname,
            "local_ip": local_ip,
            "gateway": gateway,
            "os": os_info,
            "download_bytes": total_recv,
            "upload_bytes": total_sent,
            "total_bytes": total_bytes,
            "download_bytes_formatted": format_bytes(total_recv),
            "upload_bytes_formatted": format_bytes(total_sent),
            "total_bytes_formatted": format_bytes(total_bytes),
            "download_speed": round(down_speed, 2),
            "upload_speed": round(up_speed, 2),
            "total_speed": round(tot_speed, 2),
            "download_speed_formatted": format_speed(down_speed),
            "upload_speed_formatted": format_speed(up_speed),
            "total_speed_formatted": format_speed(tot_speed),
            "packets_sent": io.packets_sent,
            "packets_recv": io.packets_recv,
            "interfaces": interfaces,
        }

    def get_interfaces(self) -> List[Dict[str, Any]]:
        """Inspect all physical and virtual network adapters on the host."""
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        io_pernic = psutil.net_io_counters(pernic=True)

        results = []
        for iface_name, addr_list in addrs.items():
            ip_val = None
            mac_val = None

            for addr in addr_list:
                # AF_INET is IPv4
                if addr.family == socket.AF_INET:
                    ip_val = addr.address
                # Link layer MAC (AF_LINK on BSD/OSX, -1 on Windows in some psutil versions)
                elif hasattr(psutil, "AF_LINK") and addr.family == psutil.AF_LINK:
                    mac_val = addr.address
                elif addr.family == -1 or "MAC" in str(addr.family):
                    mac_val = addr.address

            iface_stat = stats.get(iface_name)
            is_up = iface_stat.isup if iface_stat else False
            speed = iface_stat.speed if iface_stat else 0
            mtu = iface_stat.mtu if iface_stat else 1500

            iface_io = io_pernic.get(iface_name)
            bytes_recv = iface_io.bytes_recv if iface_io else 0
            bytes_sent = iface_io.bytes_sent if iface_io else 0

            results.append({
                "name": iface_name,
                "ip": ip_val or "Unassigned",
                "mac": normalize_mac(mac_val) or "N/A",
                "is_up": is_up,
                "speed_mbps": speed,
                "mtu": mtu,
                "bytes_recv": bytes_recv,
                "bytes_sent": bytes_sent,
                "bytes_recv_formatted": format_bytes(bytes_recv),
                "bytes_sent_formatted": format_bytes(bytes_sent),
            })

        return results


network_monitor = NetworkMonitor()

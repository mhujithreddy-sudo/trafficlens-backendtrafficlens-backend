"""
Device discovery service.
Discovers local interfaces and LAN neighbors via ARP cache and socket inspection,
persists devices to the database, and tracks cumulative device usage.
"""

import socket
import subprocess
import platform
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import psutil

from app.core.logging_config import logger
from app.core.database import SessionLocal
from app.models.device import Device
from app.models.traffic import TrafficRecord
from app.utils.network_utils import format_bytes, normalize_mac, resolve_hostname_safely, is_private_ip


class DeviceDiscoveryService:
    """Discovers host network adapters and local network neighbors."""

    def __init__(self):
        self._hostname_cache: Dict[str, str] = {}
        self._limitation_note = (
            "Per-device bandwidth accounting across external LAN nodes requires router/gateway "
            "SNMP monitoring or promiscuous packet capture. Real hardware traffic counters "
            "are provided for local system network interfaces."
        )

    def discover_devices(self) -> List[Dict[str, Any]]:
        """
        Identify host interfaces and local network neighbors.
        Updates the database Device table and returns formatted device list.
        """
        discovered: List[Dict[str, Any]] = []

        # 1. Local hardware & virtual network interfaces
        interfaces = self._get_local_interfaces()
        discovered.extend(interfaces)

        # 2. Local network neighbors via ARP cache table
        neighbors = self._get_arp_neighbors()
        discovered.extend(neighbors)

        # 3. Synchronize with database
        self._sync_devices_to_db(discovered)

        return discovered

    def _get_local_interfaces(self) -> List[Dict[str, Any]]:
        """Extract all system network interfaces with actual I/O byte counters."""
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        io_pernic = psutil.net_io_counters(pernic=True)

        devices = []
        for iface_name, addr_list in addrs.items():
            ip_val = None
            mac_val = None

            for addr in addr_list:
                if addr.family == socket.AF_INET:
                    ip_val = addr.address
                elif addr.family == -1 or hasattr(psutil, "AF_LINK") and addr.family == getattr(psutil, "AF_LINK", -99):
                    mac_val = addr.address
                elif "MAC" in str(addr.family):
                    mac_val = addr.address

            iface_stat = stats.get(iface_name)
            is_up = iface_stat.isup if iface_stat else False
            speed = iface_stat.speed if iface_stat else 0

            io = io_pernic.get(iface_name)
            down_bytes = io.bytes_recv if io else 0
            up_bytes = io.bytes_sent if io else 0
            tot_bytes = down_bytes + up_bytes

            # Friendly name
            display_name = f"{iface_name} (Local Interface)" if "Loopback" not in iface_name else iface_name

            devices.append({
                "device_name": display_name,
                "hostname": socket.gethostname(),
                "interface": iface_name,
                "ip_address": ip_val or "Unassigned",
                "mac_address": normalize_mac(mac_val) or "N/A",
                "device_type": "interface",
                "status": "online" if is_up else "offline",
                "download_usage": down_bytes,
                "upload_usage": up_bytes,
                "total_usage": tot_bytes,
                "download_bytes": down_bytes,
                "upload_bytes": up_bytes,
                "download_usage_formatted": format_bytes(down_bytes),
                "upload_usage_formatted": format_bytes(up_bytes),
                "total_usage_formatted": format_bytes(tot_bytes),
                "speed_mbps": speed,
                "is_local": True,
            })
        return devices

    def _get_arp_neighbors(self) -> List[Dict[str, Any]]:
        """Parse operating system ARP cache for active LAN nodes."""
        neighbors = []
        try:
            cmd = "arp -a"
            output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)

            # Regex for IP and MAC in ARP output
            # Matches IPv4: \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}
            # Matches MAC: (?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}
            arp_pattern = re.compile(
                r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+([0-9a-fA-F]{2}(?:[:-][0-9a-fA-F]{2}){5})\s+(\w+)"
            )

            for line in output.splitlines():
                match = arp_pattern.search(line)
                if match:
                    ip, mac, arp_type = match.groups()
                    mac_norm = normalize_mac(mac)

                    # Filter out multicast/broadcast addresses
                    if ip.startswith("224.") or ip.startswith("239.") or ip.endswith(".255"):
                        continue
                    if mac_norm in ("FF:FF:FF:FF:FF:FF", "01:00:5E:00:00:00"):
                        continue

                    # Attempt cached hostname resolution
                    if ip not in self._hostname_cache:
                        resolved = resolve_hostname_safely(ip, timeout=0.1)
                        self._hostname_cache[ip] = resolved or f"LAN-Host-{ip.split('.')[-1]}"

                    hostname = self._hostname_cache[ip]

                    neighbors.append({
                        "device_name": hostname,
                        "hostname": hostname,
                        "interface": "LAN",
                        "ip_address": ip,
                        "mac_address": mac_norm,
                        "device_type": "lan_neighbor",
                        "status": "online",
                        "download_usage": 0,
                        "upload_usage": 0,
                        "total_usage": 0,
                        "download_bytes": 0,
                        "upload_bytes": 0,
                        "download_usage_formatted": "0.00 B",
                        "upload_usage_formatted": "0.00 B",
                        "total_usage_formatted": "0.00 B",
                        "speed_mbps": 0,
                        "is_local": False,
                    })
        except Exception as exc:
            logger.debug(f"ARP cache inspection notice: {exc}")

        return neighbors

    def _sync_devices_to_db(self, devices: List[Dict[str, Any]]) -> None:
        """Upsert discovered devices into the database Device table."""
        try:
            with SessionLocal() as db:
                now_utc = datetime.now(timezone.utc)
                for dev_dict in devices:
                    ip = dev_dict.get("ip_address")
                    if not ip or ip == "Unassigned":
                        continue

                    existing = db.query(Device).filter(Device.ip_address == ip).first()
                    if existing:
                        existing.last_seen = now_utc
                        existing.status = dev_dict.get("status", "online")
                        if dev_dict.get("is_local"):
                            existing.download_bytes = dev_dict["download_usage"]
                            existing.upload_bytes = dev_dict["upload_usage"]
                        dev_dict["id"] = existing.id
                    else:
                        new_dev = Device(
                            hostname=dev_dict.get("hostname"),
                            ip_address=ip,
                            mac_address=dev_dict.get("mac_address"),
                            device_type=dev_dict.get("device_type", "unknown"),
                            status=dev_dict.get("status", "online"),
                            first_seen=now_utc,
                            last_seen=now_utc,
                            download_bytes=dev_dict.get("download_usage", 0),
                            upload_bytes=dev_dict.get("upload_usage", 0),
                        )
                        db.add(new_dev)
                        db.flush()
                        dev_dict["id"] = new_dev.id
                db.commit()
        except Exception as exc:
            logger.error(f"Error syncing devices to database: {exc}")

    def get_device_by_id(self, device_id: int) -> Optional[Dict[str, Any]]:
        """Fetch details for a specific device by its database ID."""
        try:
            with SessionLocal() as db:
                dev = db.query(Device).filter(Device.id == device_id).first()
                if not dev:
                    return None

                # Query recent traffic records for this device
                traffic_records = (
                    db.query(TrafficRecord)
                    .filter((TrafficRecord.source_ip == dev.ip_address) | (TrafficRecord.destination_ip == dev.ip_address))
                    .order_by(TrafficRecord.timestamp.desc())
                    .limit(20)
                    .all()
                )

                recent_traffic = [
                    {
                        "id": tr.id,
                        "timestamp": tr.timestamp.isoformat(),
                        "source_ip": tr.source_ip,
                        "destination_ip": tr.destination_ip,
                        "source_port": tr.source_port,
                        "destination_port": tr.destination_port,
                        "protocol": tr.protocol,
                        "bytes": tr.bytes,
                        "service": tr.service,
                    }
                    for tr in traffic_records
                ]

                total_usage = dev.download_bytes + dev.upload_bytes
                return {
                    "device": {
                        "id": dev.id,
                        "device_name": dev.hostname or f"Device-{dev.id}",
                        "hostname": dev.hostname,
                        "ip_address": dev.ip_address,
                        "mac_address": dev.mac_address,
                        "device_type": dev.device_type,
                        "status": dev.status,
                        "download_usage": dev.download_bytes,
                        "upload_usage": dev.upload_bytes,
                        "total_usage": total_usage,
                        "download_bytes": dev.download_bytes,
                        "upload_bytes": dev.upload_bytes,
                        "download_usage_formatted": format_bytes(dev.download_bytes),
                        "upload_usage_formatted": format_bytes(dev.upload_bytes),
                        "total_usage_formatted": format_bytes(total_usage),
                        "is_local": dev.device_type == "interface",
                        "first_seen": dev.first_seen.isoformat() if dev.first_seen else None,
                        "last_seen": dev.last_seen.isoformat() if dev.last_seen else None,
                    },
                    "recent_traffic": recent_traffic,
                    "top_services": [],
                }
        except Exception as exc:
            logger.error(f"Error fetching device {device_id}: {exc}")
            return None


device_discovery = DeviceDiscoveryService()

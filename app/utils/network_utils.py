"""
Network helper functions: byte formatting, speed calculations, IP/MAC utilities.
"""

import socket
import ipaddress
from typing import Optional, Union


def format_bytes(num_bytes: Union[int, float]) -> str:
    """Format bytes into a human-readable string (B, KB, MB, GB, TB)."""
    if num_bytes is None or num_bytes < 0:
        return "0.00 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    value = float(num_bytes)
    idx = 0
    while value >= 1024.0 and idx < len(units) - 1:
        value /= 1024.0
        idx += 1
    return f"{value:.2f} {units[idx]}"


def format_speed(bytes_per_sec: float) -> str:
    """Format bytes/sec into a human-readable speed string (e.g. 1.46 KB/s, 24.50 MB/s)."""
    if bytes_per_sec is None or bytes_per_sec < 0:
        return "0.00 B/s"
    return f"{format_bytes(bytes_per_sec)}/s"


def bytes_to_mbps(byte_count: Union[int, float], dt_seconds: float) -> float:
    """
    Convert a delta in bytes over a duration in seconds into Megabits per second (Mbps).
    Formula: (bytes * 8 bits/byte) / (dt_seconds * 1,000,000 bits/Mb)
    """
    if dt_seconds <= 0 or byte_count <= 0:
        return 0.0
    return round((float(byte_count) * 8.0) / (dt_seconds * 1_000_000.0), 4)


def is_private_ip(ip_str: str) -> bool:
    """Check if an IP address string is in private or loopback ranges."""
    try:
        ip_obj = ipaddress.ip_address(ip_str.strip())
        return ip_obj.is_private or ip_obj.is_loopback
    except ValueError:
        return False


def is_valid_ip(ip_str: str) -> bool:
    """Validate if an IP string is a valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(ip_str.strip())
        return True
    except ValueError:
        return False


def normalize_mac(mac: Optional[str]) -> Optional[str]:
    """Normalize MAC address string to standard uppercase colon-separated format."""
    if not mac:
        return None
    cleaned = mac.strip().replace("-", ":").upper()
    parts = cleaned.split(":")
    if len(parts) == 6 and all(len(p) <= 2 for p in parts):
        return ":".join(p.zfill(2) for p in parts)
    return cleaned


def resolve_hostname_safely(ip_str: str, timeout: float = 0.3) -> Optional[str]:
    """
    Safely perform reverse DNS lookup for an IP address with a strict timeout.
    Returns None if resolution fails or times out.
    """
    if not is_valid_ip(ip_str):
        return None
    try:
        orig_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        try:
            hostname, _, _ = socket.gethostbyaddr(ip_str)
            return hostname
        finally:
            socket.setdefaulttimeout(orig_timeout)
    except Exception:
        return None

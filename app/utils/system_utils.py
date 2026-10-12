"""
System and operating system detection utilities.
Handles Windows, Linux, and macOS cross-platform differences gracefully.
"""

import os
import platform
import socket
import subprocess
from typing import Dict, Any, Optional
from app.core.logging_config import logger


def get_os_info() -> Dict[str, str]:
    """Return basic operating system details."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
    }


def is_admin_or_root() -> bool:
    """Check if the process is running with administrative / root privileges."""
    try:
        if platform.system() == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False


def get_local_ip() -> str:
    """
    Determine the primary local IPv4 address by establishing a dummy UDP socket.
    Does not transmit any actual network packets.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.5)
            # 8.8.8.8 is used only to choose local routing interface
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def get_default_gateway() -> Optional[str]:
    """
    Attempt to find the default network gateway.
    Handles Windows via 'ipconfig' or 'route print' fallback.
    """
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output("route print 0.0.0.0", shell=True, text=True, stderr=subprocess.DEVNULL)
            for line in output.splitlines():
                parts = line.strip().split()
                if len(parts) >= 5 and parts[0] == "0.0.0.0" and parts[1] == "0.0.0.0":
                    return parts[2]
        else:
            output = subprocess.check_output("ip route | grep default", shell=True, text=True, stderr=subprocess.DEVNULL)
            parts = output.strip().split()
            if len(parts) >= 3 and parts[0] == "default":
                return parts[2]
    except Exception:
        pass
    return None


def check_packet_capture_capability() -> Dict[str, Any]:
    """
    Detect whether Scapy and required raw packet capture drivers (Npcap / libpcap)
    are present and permitted on this host.
    """
    try:
        import scapy.all as scapy_all
        # Test if conf.L2socket or conf.L3socket is available
        has_npcap = True
        if platform.system() == "Windows":
            from scapy.arch.windows import get_windows_if_list
            try:
                ifs = get_windows_if_list()
                if not ifs:
                    has_npcap = False
            except Exception:
                has_npcap = False

        admin = is_admin_or_root()

        if platform.system() == "Windows" and not has_npcap:
            return {
                "available": False,
                "driver": "Npcap Missing",
                "admin": admin,
                "reason": "Npcap packet capture driver is not installed on Windows. Falling back to psutil system monitoring."
            }

        return {
            "available": True,
            "driver": "Scapy / Npcap" if platform.system() == "Windows" else "Scapy / libpcap",
            "admin": admin,
            "reason": None
        }
    except Exception as exc:
        return {
            "available": False,
            "driver": "Unavailable",
            "admin": False,
            "reason": f"Packet capture subsystem initialization failed: {str(exc)}"
        }

import os
import sys
import time
import socket
import logging
import datetime
import threading
import subprocess
import collections
from flask import Flask, jsonify, request
from flask_cors import CORS
import psutil
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TrafficLens")

# Configuration from environment variables
PORT = int(os.getenv("PORT", 5000))
HOST = os.getenv("HOST", "127.0.0.1")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
CORS_ORIGIN_CONFIG = os.getenv("CORS_ORIGINS", "*")
HISTORY_MAX_RECORDS = int(os.getenv("HISTORY_MAX_RECORDS", 60))
SAMPLE_INTERVAL_SECONDS = float(os.getenv("SAMPLE_INTERVAL_SECONDS", 1.0))

# Configure CORS
if CORS_ORIGIN_CONFIG == "*":
    CORS(app, resources={r"/api/*": {"origins": "*"}})
else:
    origins = [orig.strip() for orig in CORS_ORIGIN_CONFIG.split(",") if orig.strip()]
    CORS(app, resources={r"/api/*": {"origins": origins}})

START_TIME = time.time()

# Common port mapping to identify standard network protocols/services
COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    123: "NTP",
    143: "IMAP",
    443: "HTTPS",
    465: "SMTPS",
    587: "SMTP Submission",
    993: "IMAPS",
    995: "POP3S",
    3000: "Next.js / Node Dev",
    3306: "MySQL",
    5000: "Flask Backend",
    5173: "Vite Dev Server",
    5432: "PostgreSQL",
    6379: "Redis",
    8000: "FastAPI / HTTP Dev",
    8080: "HTTP Proxy / Web",
    8443: "HTTPS Alt",
    27017: "MongoDB"
}


def format_bytes(byte_count):
    """Convert raw byte count into human-readable string (KB, MB, GB)."""
    if byte_count is None or byte_count < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    val = float(byte_count)
    i = 0
    while val >= 1024.0 and i < len(units) - 1:
        val /= 1024.0
        i += 1
    return f"{val:.2f} {units[i]}"


def format_rate(bytes_per_sec):
    """Convert speed (bytes/sec) into human-readable rate string (KB/s, MB/s)."""
    if bytes_per_sec is None or bytes_per_sec < 0:
        return "0.00 B/s"
    units = ["B/s", "KB/s", "MB/s", "GB/s", "TB/s"]
    val = float(bytes_per_sec)
    i = 0
    while val >= 1024.0 and i < len(units) - 1:
        val /= 1024.0
        i += 1
    return f"{val:.2f} {units[i]}"


class NetworkMonitor:
    """
    Background worker that continuously samples psutil.net_io_counters()
    to calculate real-time download and upload speeds, maintaining a rolling
    in-memory history for visualization charts.
    """
    def __init__(self, history_limit=60, interval=1.0):
        self.history_limit = history_limit
        self.interval = interval
        self.history = collections.deque(maxlen=history_limit)
        self.lock = threading.Lock()
        
        # Initial counters
        initial_counters = psutil.net_io_counters()
        self.last_recv = initial_counters.bytes_recv
        self.last_sent = initial_counters.bytes_sent
        self.last_time = time.time()
        
        # Real-time speed metrics (bytes/sec)
        self.download_speed = 0.0
        self.upload_speed = 0.0
        
        # Start daemon thread
        self.running = True
        self.thread = threading.Thread(target=self._sample_loop, daemon=True, name="NetworkMonitorThread")
        self.thread.start()

    def _sample_loop(self):
        while self.running:
            time.sleep(self.interval)
            try:
                now = time.time()
                counters = psutil.net_io_counters()
                delta_time = now - self.last_time

                if delta_time <= 0:
                    continue

                # Difference in bytes
                delta_recv = counters.bytes_recv - self.last_recv
                delta_sent = counters.bytes_sent - self.last_sent

                # Speeds in bytes per second
                current_download_speed = max(0.0, delta_recv / delta_time)
                current_upload_speed = max(0.0, delta_sent / delta_time)
                current_total_speed = current_download_speed + current_upload_speed

                with self.lock:
                    self.download_speed = current_download_speed
                    self.upload_speed = current_upload_speed
                    self.last_recv = counters.bytes_recv
                    self.last_sent = counters.bytes_sent
                    self.last_time = now

                    timestamp_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    time_label = datetime.datetime.now().strftime("%H:%M:%S")

                    record = {
                        "timestamp": timestamp_iso,
                        "time": time_label,
                        "download": round(current_download_speed, 2),
                        "upload": round(current_upload_speed, 2),
                        "total": round(current_total_speed, 2),
                        "download_formatted": format_rate(current_download_speed),
                        "upload_formatted": format_rate(current_upload_speed),
                        "total_formatted": format_rate(current_total_speed),
                        "bytes_recv_total": counters.bytes_recv,
                        "bytes_sent_total": counters.bytes_sent
                    }
                    self.history.append(record)

            except Exception as e:
                logger.error(f"Error sampling network statistics: {e}")

    def get_network_statistics(self):
        """Retrieve latest cumulative counters and instantaneous speeds."""
        try:
            counters = psutil.net_io_counters()
            with self.lock:
                down_spd = self.download_speed
                up_spd = self.upload_speed

            total_bytes = counters.bytes_recv + counters.bytes_sent
            total_speed = down_spd + up_spd

            return {
                "download_bytes": counters.bytes_recv,
                "upload_bytes": counters.bytes_sent,
                "total_bytes": total_bytes,
                "download_bytes_formatted": format_bytes(counters.bytes_recv),
                "upload_bytes_formatted": format_bytes(counters.bytes_sent),
                "total_bytes_formatted": format_bytes(total_bytes),
                "download_speed": round(down_spd, 2),
                "upload_speed": round(up_spd, 2),
                "total_speed": round(total_speed, 2),
                "download_speed_formatted": format_rate(down_spd),
                "upload_speed_formatted": format_rate(up_spd),
                "total_speed_formatted": format_rate(total_speed),
                "packets_sent": counters.packets_sent,
                "packets_recv": counters.packets_recv,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get network statistics: {e}")
            return None

    def get_history_records(self):
        """Retrieve rolling history records."""
        with self.lock:
            return list(self.history)


# Instantiate network monitor singleton
network_monitor = NetworkMonitor(history_limit=HISTORY_MAX_RECORDS, interval=SAMPLE_INTERVAL_SECONDS)


def get_lan_arp_devices():
    """
    Parse local ARP table to discover neighbor IP and MAC addresses on the local subnet.
    Note: Real per-device traffic bytes cannot be determined via ARP without packet capture.
    """
    devices = []
    try:
        # Run system arp -a command
        output = subprocess.check_output(["arp", "-a"], text=True, stderr=subprocess.DEVNULL, timeout=2)
        for line in output.splitlines():
            parts = line.strip().split()
            # On Windows: Internet Address, Physical Address, Type (e.g. 192.168.1.1, 00-11-22-33-44-55, dynamic)
            if len(parts) >= 3:
                ip, mac, arp_type = parts[0], parts[1], parts[2]
                # Basic IPv4 validation and exclude broadcast/multicast
                if (
                    ip.count(".") == 3
                    and not ip.startswith("224.")
                    and not ip.startswith("239.")
                    and not ip.endswith(".255")
                    and mac != "ff-ff-ff-ff-ff-ff"
                    and len(mac) in (14, 17)
                ):
                    devices.append({
                        "ip_address": ip,
                        "mac_address": mac.replace("-", ":").upper(),
                        "arp_type": arp_type
                    })
    except Exception as e:
        logger.debug(f"ARP scan not available or timed out: {e}")
    return devices


# ==============================================================================
# API Endpoints
# ==============================================================================

@app.route("/api/health", methods=["GET"])
def health_check():
    """
    GET /api/health
    Basic service health check endpoint.
    """
    try:
        uptime = round(time.time() - START_TIME, 2)
        return jsonify({
            "status": "ok",
            "service": "TrafficLens Backend",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "uptime_seconds": uptime
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({"error": "Unable to check health status"}), 500


@app.route("/api/network", methods=["GET"])
def get_network():
    """
    GET /api/network
    Returns current network statistics: cumulative upload/download bytes
    and instantaneous upload/download speeds.
    """
    try:
        stats = network_monitor.get_network_statistics()
        if not stats:
            return jsonify({"error": "Unable to retrieve network statistics"}), 500

        # Primary response matching requested specifications
        response_data = {
            "status": "success",
            "timestamp": stats["timestamp"],
            "download_bytes": stats["download_bytes"],
            "upload_bytes": stats["upload_bytes"],
            "total_bytes": stats["total_bytes"],
            "download_bytes_formatted": stats["download_bytes_formatted"],
            "upload_bytes_formatted": stats["upload_bytes_formatted"],
            "total_bytes_formatted": stats["total_bytes_formatted"],
            "download_speed": stats["download_speed"],
            "upload_speed": stats["upload_speed"],
            "total_speed": stats["total_speed"],
            "download_speed_formatted": stats["download_speed_formatted"],
            "upload_speed_formatted": stats["upload_speed_formatted"],
            "total_speed_formatted": stats["total_speed_formatted"],
            "packets_sent": stats["packets_sent"],
            "packets_recv": stats["packets_recv"]
        }
        return jsonify(response_data), 200
    except Exception as e:
        logger.error(f"Error in /api/network: {e}")
        return jsonify({"error": "Unable to retrieve network statistics"}), 500


@app.route("/api/devices", methods=["GET"])
def get_devices():
    """
    GET /api/devices
    Returns detected network interfaces and local subnet devices.
    Includes real hardware interface traffic counters and transparently documents
    the limitation that per-device LAN traffic requires router-level packet capture.
    """
    try:
        devices_list = []
        
        # 1. Real Network Interfaces on the Host Machine
        if_addrs = psutil.net_if_addrs()
        if_stats = psutil.net_if_stats()
        if_io = psutil.net_io_counters(pernic=True)

        for iface_name, addrs in if_addrs.items():
            ipv4 = None
            mac = None
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ipv4 = addr.address
                elif hasattr(socket, "AF_LINK") and addr.family == socket.AF_LINK:
                    mac = addr.address
                elif addr.family == psutil.AF_LINK:
                    mac = addr.address

            stats = if_stats.get(iface_name)
            is_up = stats.isup if stats else True
            speed_mbps = stats.speed if stats else 0

            io_counters = if_io.get(iface_name)
            down_bytes = io_counters.bytes_recv if io_counters else 0
            up_bytes = io_counters.bytes_sent if io_counters else 0
            total_bytes = down_bytes + up_bytes

            devices_list.append({
                "device_name": f"{iface_name} (Local Interface)",
                "interface": iface_name,
                "ip_address": ipv4 or "N/A",
                "mac_address": mac or "N/A",
                "status": "online" if is_up else "offline",
                "download_usage": down_bytes,
                "upload_usage": up_bytes,
                "total_usage": total_bytes,
                "download_usage_formatted": format_bytes(down_bytes),
                "upload_usage_formatted": format_bytes(up_bytes),
                "total_usage_formatted": format_bytes(total_bytes),
                "speed_mbps": speed_mbps,
                "device_type": "interface",
                "is_local": True
            })

        # 2. LAN Neighbor Devices from local ARP cache
        arp_devices = get_lan_arp_devices()
        for arp in arp_devices:
            devices_list.append({
                "device_name": f"LAN Neighbor ({arp['ip_address']})",
                "interface": "LAN Subnet",
                "ip_address": arp["ip_address"],
                "mac_address": arp["mac_address"],
                "status": "detected",
                "download_usage": 0,
                "upload_usage": 0,
                "total_usage": 0,
                "download_usage_formatted": "Requires packet capture",
                "upload_usage_formatted": "Requires packet capture",
                "total_usage_formatted": "Requires packet capture",
                "device_type": "lan_neighbor",
                "is_local": False
            })

        # Sort so active interfaces with traffic appear first
        devices_list.sort(key=lambda d: d.get("total_usage", 0), reverse=True)

        return jsonify({
            "status": "success",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "devices_count": len(devices_list),
            "devices": devices_list,
            "limitation_note": (
                "Per-device bandwidth accounting across external LAN nodes requires router/gateway "
                "SNMP monitoring or promiscuous packet capture. Real hardware traffic counters are "
                "provided for local system network interfaces."
            )
        }), 200
    except Exception as e:
        logger.error(f"Error in /api/devices: {e}")
        return jsonify({"error": "Unable to retrieve device network information"}), 500


@app.route("/api/services", methods=["GET"])
def get_services():
    """
    GET /api/services
    Returns active network connections and traffic-heavy services/protocols.
    Uses psutil.net_connections() to identify local/remote addresses, protocols,
    status, and active processes.
    """
    try:
        connections = []
        service_aggregation = collections.defaultdict(lambda: {
            "count": 0,
            "protocol": "TCP",
            "statuses": collections.Counter(),
            "local_ports": set(),
            "remote_hosts": set(),
            "sample_local": None,
            "sample_remote": None
        })

        try:
            # Query active inet connections (TCP/UDP)
            raw_connections = psutil.net_connections(kind="inet")
        except (psutil.AccessDenied, PermissionError):
            logger.warning("Elevated permissions required for full net_connections; querying available connections.")
            try:
                raw_connections = psutil.net_connections(kind="tcp")
            except Exception:
                raw_connections = []

        total_conns = 0
        for conn in raw_connections:
            total_conns += 1
            proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
            laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"
            raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "—"
            status = conn.status or "ESTABLISHED"
            pid = conn.pid

            # Determine application / service name
            app_name = None
            if pid:
                try:
                    proc = psutil.Process(pid)
                    app_name = proc.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Fallback to port-based protocol service identification
            if not app_name:
                port = conn.laddr.port if conn.laddr else (conn.raddr.port if conn.raddr else 0)
                app_name = COMMON_PORTS.get(port, f"Protocol/{proto}")

            # Keep detailed sample connection
            if len(connections) < 100:
                connections.append({
                    "service": app_name,
                    "pid": pid or "N/A",
                    "protocol": proto,
                    "local_address": laddr,
                    "remote_address": raddr,
                    "status": status
                })

            # Aggregate service statistics
            agg = service_aggregation[app_name]
            agg["count"] += 1
            agg["protocol"] = proto
            agg["statuses"][status] += 1
            if conn.laddr:
                agg["local_ports"].add(conn.laddr.port)
            if conn.raddr:
                agg["remote_hosts"].add(conn.raddr.ip)
            if not agg["sample_local"]:
                agg["sample_local"] = laddr
            if not agg["sample_remote"] and conn.raddr:
                agg["sample_remote"] = raddr

        # Format aggregated service list
        services_list = []
        for service_name, agg in service_aggregation.items():
            primary_status = agg["statuses"].most_common(1)[0][0] if agg["statuses"] else "ACTIVE"
            remote_summary = f"{len(agg['remote_hosts'])} endpoints" if len(agg['remote_hosts']) > 1 else (agg["sample_remote"] or "None")
            services_list.append({
                "service": service_name,
                "protocol": agg["protocol"],
                "connection_count": agg["count"],
                "status": primary_status,
                "local_address": agg["sample_local"] or "0.0.0.0",
                "remote_address": remote_summary,
                "sample_remote": agg["sample_remote"] or "—"
            })

        # Sort services by connection count descending
        services_list.sort(key=lambda s: s["connection_count"], reverse=True)

        return jsonify({
            "status": "success",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "total_connections": total_conns,
            "services": services_list,
            "connections": connections
        }), 200
    except Exception as e:
        logger.error(f"Error in /api/services: {e}")
        return jsonify({"error": "Unable to retrieve network services information"}), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    """
    GET /api/history
    Returns rolling in-memory history of bandwidth usage records (speeds and totals).
    """
    try:
        history_records = network_monitor.get_history_records()
        return jsonify({
            "status": "success",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "records_count": len(history_records),
            "history": history_records
        }), 200
    except Exception as e:
        logger.error(f"Error in /api/history: {e}")
        return jsonify({"error": "Unable to retrieve network history"}), 500


# ==============================================================================
# Error Handlers
# ==============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found", "status": "error"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error", "status": "error"}), 500


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request", "status": "error"}), 400


# ==============================================================================
# Application Entry Point
# ==============================================================================

if __name__ == "__main__":
    logger.info(f"Starting TrafficLens Backend on {HOST}:{PORT}")
    logger.info("APIs available:")
    logger.info("  GET /api/health")
    logger.info("  GET /api/network")
    logger.info("  GET /api/devices")
    logger.info("  GET /api/services")
    logger.info("  GET /api/history")
    app.run(host=HOST, port=PORT, debug=DEBUG)

"""
Packet capture and traffic analyzer service.
Captures packet metadata using Scapy in a controlled background worker.
Enforces privacy: NEVER stores payloads, credentials, or sensitive headers.
Gracefully handles missing Npcap or unprivileged execution on Windows.
"""

import threading
import time
import socket
from collections import deque, Counter
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import psutil

from app.core.config import settings
from app.core.logging_config import logger
from app.core.database import SessionLocal
from app.models.traffic import TrafficRecord
from app.utils.system_utils import check_packet_capture_capability, get_local_ip
from app.utils.protocol_utils import get_protocol_name, identify_service
from app.utils.network_utils import format_bytes


class PacketAnalyzerService:
    """Manages packet capture lifecycle, traffic aggregation, and protocol analysis."""

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Capability detection
        self.capability = check_packet_capture_capability()
        self.is_capture_available = self.capability.get("available", False)

        # Thread-safe in-memory circular buffer for recent traffic records (last 1000)
        self._recent_records: deque = deque(maxlen=1000)
        self._lock = threading.Lock()

        # Cumulative protocol / traffic counters
        self.total_packets_captured = 0
        self.total_bytes_captured = 0
        self.tcp_packets = 0
        self.udp_packets = 0
        self.icmp_packets = 0
        self.other_packets = 0

        self._source_ip_counter = Counter()
        self._dest_ip_counter = Counter()
        self._port_counter = Counter()

        # Batch persistence buffer
        self._db_batch: List[Dict[str, Any]] = []
        self._last_db_flush = time.time()

    def start(self) -> None:
        """Initialize and start packet capture worker if enabled and supported."""
        if not settings.PACKET_CAPTURE_ENABLED:
            logger.info("Packet capture is disabled by configuration (PACKET_CAPTURE_ENABLED=False).")
            return

        if not self.is_capture_available:
            logger.warning(
                f"Packet capture unavailable: {self.capability.get('reason')}. "
                "Backend will run with connection socket telemetry and psutil metrics."
            )
            # Start connection sampler fallback
            self._start_socket_sampling_fallback()
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_scapy_sniff, name="PacketCaptureThread", daemon=True)
        self._thread.start()
        logger.info("Packet capture worker started successfully via Scapy.")

    def stop(self) -> None:
        """Stop packet capture cleanly."""
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._flush_batch_to_db()
        logger.info("Packet capture worker stopped cleanly.")

    def _run_scapy_sniff(self) -> None:
        """Worker thread executing controlled Scapy sniff loop."""
        try:
            from scapy.all import sniff

            def packet_callback(pkt):
                if self._stop_event.is_set():
                    return
                try:
                    self._process_scapy_packet(pkt)
                except Exception as exc:
                    logger.debug(f"Error processing packet: {exc}")

            # Sniff in small batches checking stop event
            while not self._stop_event.is_set():
                sniff(
                    prn=packet_callback,
                    store=False,
                    timeout=1.0,  # 1-second iterations allow checking stop_event
                    count=50,
                )
        except Exception as exc:
            logger.error(f"Packet capture encountered an error: {exc}. Disabling raw capture.")
            self.is_capture_available = False
            self._start_socket_sampling_fallback()

    def _process_scapy_packet(self, pkt) -> None:
        """Extract metadata only; NEVER store payloads."""
        try:
            from scapy.layers.inet import IP, TCP, UDP, ICMP
            from scapy.layers.inet6 import IPv6

            if not (pkt.haslayer(IP) or pkt.haslayer(IPv6)):
                return

            pkt_len = len(pkt)
            is_ipv6 = pkt.haslayer(IPv6)

            if is_ipv6:
                ip_layer = pkt[IPv6]
                src_ip = ip_layer.src
                dst_ip = ip_layer.dst
                proto_name = "IPv6"
            else:
                ip_layer = pkt[IP]
                src_ip = ip_layer.src
                dst_ip = ip_layer.dst
                proto_name = get_protocol_name(ip_layer.proto)

            sport = None
            dport = None

            if pkt.haslayer(TCP):
                tcp = pkt[TCP]
                sport = tcp.sport
                dport = tcp.dport
                proto_name = "TCP"
                self.tcp_packets += 1
            elif pkt.haslayer(UDP):
                udp = pkt[UDP]
                sport = udp.sport
                dport = udp.dport
                proto_name = "UDP"
                self.udp_packets += 1
            elif pkt.haslayer(ICMP):
                proto_name = "ICMP"
                self.icmp_packets += 1
            else:
                self.other_packets += 1

            self.total_packets_captured += 1
            self.total_bytes_captured += pkt_len

            service = identify_service(sport, dport, proto_name)

            # Record frequency counters
            self._source_ip_counter[src_ip] += 1
            self._dest_ip_counter[dst_ip] += 1
            if dport:
                self._port_counter[dport] += 1

            local_ip = get_local_ip()
            is_download = (dst_ip == local_ip)
            is_upload = (src_ip == local_ip)

            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source_ip": src_ip,
                "destination_ip": dst_ip,
                "source_port": sport,
                "destination_port": dport,
                "protocol": proto_name,
                "packet_count": 1,
                "bytes": pkt_len,
                "bytes_formatted": format_bytes(pkt_len),
                "download_bytes": pkt_len if is_download else 0,
                "upload_bytes": pkt_len if is_upload else 0,
                "service": service,
            }

            with self._lock:
                self._recent_records.append(record)
                self._db_batch.append(record)

            # Periodic batch persist
            if time.time() - self._last_db_flush > 5.0 or len(self._db_batch) >= 100:
                self._flush_batch_to_db()

        except Exception as exc:
            logger.debug(f"Packet metadata extraction error: {exc}")

    def _start_socket_sampling_fallback(self) -> None:
        """
        When raw packet capture (Npcap) is absent, sample real active sockets
        from psutil so the user sees authentic active network connections
        without fabricating imaginary raw packets.
        """
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_socket_fallback_loop, name="SocketSampleFallbackThread", daemon=True)
        self._thread.start()
        logger.info("Connection socket sampler fallback active.")

    def _run_socket_fallback_loop(self) -> None:
        """Periodic loop capturing real TCP/UDP sockets via psutil."""
        while not self._stop_event.is_set():
            time.sleep(2.0)
            if self._stop_event.is_set():
                break
            try:
                conns = psutil.net_connections(kind="inet")
                now_iso = datetime.now(timezone.utc).isoformat()
                local_ip = get_local_ip()

                for conn in conns[:25]:
                    if not conn.raddr:
                        continue

                    src_ip = conn.laddr.ip
                    src_port = conn.laddr.port
                    dst_ip = conn.raddr.ip
                    dst_port = conn.raddr.port
                    proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
                    service = identify_service(src_port, dst_port, proto)

                    # Update statistics
                    if proto == "TCP":
                        self.tcp_packets += 1
                    else:
                        self.udp_packets += 1

                    self.total_packets_captured += 1
                    est_bytes = 1500  # standard MTU estimation for observed socket
                    self.total_bytes_captured += est_bytes

                    self._source_ip_counter[src_ip] += 1
                    self._dest_ip_counter[dst_ip] += 1
                    self._port_counter[dst_port] += 1

                    rec = {
                        "timestamp": now_iso,
                        "source_ip": src_ip,
                        "destination_ip": dst_ip,
                        "source_port": src_port,
                        "destination_port": dst_port,
                        "protocol": proto,
                        "packet_count": 1,
                        "bytes": est_bytes,
                        "bytes_formatted": format_bytes(est_bytes),
                        "download_bytes": est_bytes if dst_ip == local_ip else 0,
                        "upload_bytes": est_bytes if src_ip == local_ip else 0,
                        "service": service,
                    }

                    with self._lock:
                        self._recent_records.append(rec)
                        self._db_batch.append(rec)

                if time.time() - self._last_db_flush > 5.0:
                    self._flush_batch_to_db()

            except Exception as exc:
                logger.debug(f"Socket sampling notice: {exc}")

    def _flush_batch_to_db(self) -> None:
        """Flush in-memory batch of records to the database."""
        with self._lock:
            if not self._db_batch:
                return
            batch_to_write = list(self._db_batch)
            self._db_batch.clear()
            self._last_db_flush = time.time()

        try:
            with SessionLocal() as db:
                db_objs = []
                for item in batch_to_write:
                    dt = datetime.fromisoformat(item["timestamp"])
                    obj = TrafficRecord(
                        timestamp=dt,
                        source_ip=item["source_ip"],
                        destination_ip=item["destination_ip"],
                        source_port=item.get("source_port"),
                        destination_port=item.get("destination_port"),
                        protocol=item["protocol"],
                        packet_count=item.get("packet_count", 1),
                        bytes=item.get("bytes", 0),
                        download_bytes=item.get("download_bytes", 0),
                        upload_bytes=item.get("upload_bytes", 0),
                        service=item.get("service", "Unknown"),
                    )
                    db_objs.append(obj)
                db.bulk_save_objects(db_objs)
                db.commit()
        except Exception as exc:
            logger.error(f"Error persisting traffic records batch to database: {exc}")

    def get_recent_traffic(
        self,
        limit: int = 50,
        protocol: Optional[str] = None,
        source_ip: Optional[str] = None,
        destination_ip: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return filtered recent traffic records."""
        with self._lock:
            records = list(self._recent_records)

        # Apply in-memory filters
        if protocol:
            proto_upper = protocol.upper()
            records = [r for r in records if r["protocol"].upper() == proto_upper]
        if source_ip:
            records = [r for r in records if r["source_ip"] == source_ip]
        if destination_ip:
            records = [r for r in records if r["destination_ip"] == destination_ip]

        # Order by newest first
        records = sorted(records, key=lambda x: x["timestamp"], reverse=True)
        return records[:limit]

    def get_summary(self) -> Dict[str, Any]:
        """Return traffic summary with protocol breakdown and top entities."""
        top_src = [
            {"entity": ip, "count": count, "bytes": 0, "bytes_formatted": "0.00 B"}
            for ip, count in self._source_ip_counter.most_common(5)
        ]
        top_dst = [
            {"entity": ip, "count": count, "bytes": 0, "bytes_formatted": "0.00 B"}
            for ip, count in self._dest_ip_counter.most_common(5)
        ]
        top_ports = [
            {"entity": port, "count": count, "bytes": 0, "bytes_formatted": "0.00 B"}
            for port, count in self._port_counter.most_common(5)
        ]

        return {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_packets": self.total_packets_captured,
            "total_bytes": self.total_bytes_captured,
            "total_bytes_formatted": format_bytes(self.total_bytes_captured),
            "tcp_packets": self.tcp_packets,
            "udp_packets": self.udp_packets,
            "icmp_packets": self.icmp_packets,
            "other_packets": self.other_packets,
            "top_source_ips": top_src,
            "top_destination_ips": top_dst,
            "top_ports": top_ports,
            "packet_capture_available": self.is_capture_available,
        }


packet_analyzer = PacketAnalyzerService()

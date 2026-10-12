"""
Bandwidth monitoring service.
Samples network I/O counters, computes rates, maintains rolling history,
persists records to database, and triggers alerts.
"""

import time
import threading
from datetime import datetime, timezone
from collections import deque
from typing import Dict, Any, List, Optional
import psutil

from app.core.config import settings
from app.core.logging_config import logger
from app.core.database import SessionLocal
from app.models.bandwidth import BandwidthRecord
from app.models.alert import Alert
from app.utils.network_utils import format_bytes, format_speed, bytes_to_mbps


class BandwidthMonitor:
    """Thread-safe background service that tracks bandwidth consumption."""

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Rolling in-memory history buffer (thread-safe operations via lock or deque)
        self._history: deque = deque(maxlen=settings.HISTORY_MAX_IN_MEMORY)
        self._lock = threading.Lock()

        # Previous sample values for delta calculation
        self._prev_time: float = time.time()
        self._prev_recv: int = 0
        self._prev_sent: int = 0
        self._prev_packets_recv: int = 0
        self._prev_packets_sent: int = 0

        # Current instantaneous measurement
        self._current_stats: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_interface": "all",
            "total_bytes_sent": 0,
            "total_bytes_recv": 0,
            "upload_speed_bps": 0.0,
            "download_speed_bps": 0.0,
            "upload_mbps": 0.0,
            "download_mbps": 0.0,
            "total_mbps": 0.0,
            "upload_speed_formatted": "0.00 B/s",
            "download_speed_formatted": "0.00 B/s",
            "total_speed_formatted": "0.00 B/s",
            "download_bytes_formatted": "0.00 B",
            "upload_bytes_formatted": "0.00 B",
            "total_bytes_formatted": "0.00 B",
            "packets_sent": 0,
            "packets_recv": 0,
            "traffic_level": "LOW",
        }

        # Peak stats tracking
        self.peak_download_mbps: float = 0.0
        self.peak_upload_mbps: float = 0.0

        # Database flush counter (e.g. flush to DB every 5 seconds)
        self._db_flush_counter = 0

    def start(self) -> None:
        """Start the background bandwidth monitoring thread."""
        if self._running:
            return

        # Initialize baseline counters
        try:
            counters = psutil.net_io_counters()
            self._prev_recv = counters.bytes_recv
            self._prev_sent = counters.bytes_sent
            self._prev_packets_recv = counters.packets_recv
            self._prev_packets_sent = counters.packets_sent
            self._prev_time = time.time()
        except Exception as exc:
            logger.warning(f"Could not read initial network counters: {exc}")

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="BandwidthMonitorThread", daemon=True)
        self._thread.start()
        logger.info("Bandwidth monitoring service started successfully.")

    def stop(self) -> None:
        """Signal the thread to stop and wait for it cleanly."""
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Bandwidth monitoring service stopped cleanly.")

    def _classify_traffic_level(self, total_mbps: float) -> str:
        """Deterministic traffic level based on configured thresholds."""
        if total_mbps < settings.TRAFFIC_LEVEL_LOW_MBPS:
            return "LOW"
        elif total_mbps < settings.TRAFFIC_LEVEL_MEDIUM_MBPS:
            return "MEDIUM"
        else:
            return "HIGH"

    def _run_loop(self) -> None:
        """Periodic background sampling loop."""
        while not self._stop_event.is_set():
            time.sleep(settings.SAMPLE_INTERVAL_SECONDS)
            if self._stop_event.is_set():
                break
            try:
                self._sample()
            except Exception as exc:
                logger.error(f"Error sampling bandwidth counters: {exc}")

    def _sample(self) -> None:
        """Take a sample, calculate speed deltas, update memory and check alerts."""
        now = time.time()
        dt = max(now - self._prev_time, 0.001)

        counters = psutil.net_io_counters()
        curr_recv = counters.bytes_recv
        curr_sent = counters.bytes_sent
        curr_pkts_recv = counters.packets_recv
        curr_pkts_sent = counters.packets_sent

        # Compute delta (guarding against counter reset / reboot)
        delta_recv = max(0, curr_recv - self._prev_recv)
        delta_sent = max(0, curr_sent - self._prev_sent)

        # Speeds in Bytes per second
        download_speed_bps = delta_recv / dt
        upload_speed_bps = delta_sent / dt
        total_speed_bps = download_speed_bps + upload_speed_bps

        # Speeds in Megabits per second (Mbps)
        # 1 byte = 8 bits, 1 Mb = 1,000,000 bits
        download_mbps = bytes_to_mbps(delta_recv, dt)
        upload_mbps = bytes_to_mbps(delta_sent, dt)
        total_mbps = round(download_mbps + upload_mbps, 4)

        # Update peak counters
        if download_mbps > self.peak_download_mbps:
            self.peak_download_mbps = download_mbps
        if upload_mbps > self.peak_upload_mbps:
            self.peak_upload_mbps = upload_mbps

        traffic_level = self._classify_traffic_level(total_mbps)

        now_dt = datetime.now(timezone.utc)
        iso_time = now_dt.isoformat()
        hh_mm_ss = now_dt.strftime("%H:%M:%S")

        sample_dict = {
            "timestamp": iso_time,
            "time": hh_mm_ss,
            "active_interface": "all",
            "total_bytes_sent": curr_sent,
            "total_bytes_recv": curr_recv,
            "upload_speed_bps": round(upload_speed_bps, 2),
            "download_speed_bps": round(download_speed_bps, 2),
            "upload_mbps": upload_mbps,
            "download_mbps": download_mbps,
            "total_mbps": total_mbps,
            # Backwards compatibility fields for frontend
            "download": round(download_speed_bps, 2),
            "upload": round(upload_speed_bps, 2),
            "total": round(total_speed_bps, 2),
            "upload_speed_formatted": format_speed(upload_speed_bps),
            "download_speed_formatted": format_speed(download_speed_bps),
            "total_speed_formatted": format_speed(total_speed_bps),
            "download_formatted": format_speed(download_speed_bps),
            "upload_formatted": format_speed(upload_speed_bps),
            "total_formatted": format_speed(total_speed_bps),
            "download_bytes_formatted": format_bytes(curr_recv),
            "upload_bytes_formatted": format_bytes(curr_sent),
            "total_bytes_formatted": format_bytes(curr_recv + curr_sent),
            "packets_sent": curr_pkts_sent,
            "packets_recv": curr_pkts_recv,
            "traffic_level": traffic_level,
        }

        with self._lock:
            self._current_stats = sample_dict
            self._history.append(sample_dict)

        # Update previous markers
        self._prev_time = now
        self._prev_recv = curr_recv
        self._prev_sent = curr_sent
        self._prev_packets_recv = curr_pkts_recv
        self._prev_packets_sent = curr_pkts_sent

        # Check for spike anomalies / alerts
        self._check_alerts(total_mbps, sample_dict)

        # Periodically flush sample to database (every 5 samples = 5 seconds)
        self._db_flush_counter += 1
        if self._db_flush_counter >= 5:
            self._db_flush_counter = 0
            self._persist_sample(now_dt, delta_recv, delta_sent, download_mbps, upload_mbps)

    def _check_alerts(self, current_mbps: float, sample: Dict[str, Any]) -> None:
        """Check for bandwidth threshold violation or anomalous traffic spike."""
        if current_mbps >= settings.BANDWIDTH_ALERT_THRESHOLD_MBPS:
            msg = (
                f"High bandwidth consumption detected: {current_mbps:.2f} Mbps "
                f"(Threshold: {settings.BANDWIDTH_ALERT_THRESHOLD_MBPS:.2f} Mbps)."
            )
            self._create_alert("bandwidth_spike", "warning", msg)

        # Check spike against rolling history
        with self._lock:
            if len(self._history) >= 10:
                past_rates = [h["total_mbps"] for h in list(self._history)[:-1]]
                avg_rate = sum(past_rates) / len(past_rates)
                if avg_rate > 1.0 and current_mbps >= (avg_rate * settings.TRAFFIC_SPIKE_FACTOR):
                    msg = (
                        f"Anomalous traffic spike: {current_mbps:.2f} Mbps is "
                        f"{current_mbps / avg_rate:.1f}x higher than recent baseline ({avg_rate:.2f} Mbps)."
                    )
                    self._create_alert("traffic_spike", "warning", msg)

    def _create_alert(self, alert_type: str, severity: str, message: str) -> None:
        """Persist an alert record in the database."""
        try:
            with SessionLocal() as db:
                alert = Alert(
                    alert_type=alert_type,
                    severity=severity,
                    message=message,
                    timestamp=datetime.now(timezone.utc),
                    resolved=False,
                )
                db.add(alert)
                db.commit()
                logger.warning(f"[ALERT] {alert_type.upper()}: {message}")
        except Exception as exc:
            logger.error(f"Failed to persist alert: {exc}")

    def _persist_sample(self, timestamp: datetime, down_bytes: int, up_bytes: int, down_mbps: float, up_mbps: float) -> None:
        """Save bandwidth record to database for historical querying."""
        try:
            with SessionLocal() as db:
                record = BandwidthRecord(
                    timestamp=timestamp,
                    interface_name="all",
                    download_bytes=down_bytes,
                    upload_bytes=up_bytes,
                    download_mbps=down_mbps,
                    upload_mbps=up_mbps,
                )
                db.add(record)
                db.commit()
        except Exception as exc:
            logger.error(f"Failed to persist bandwidth record: {exc}")

    def get_current(self) -> Dict[str, Any]:
        """Return the most recent bandwidth telemetry sample."""
        with self._lock:
            return dict(self._current_stats)

    def get_history(self, limit: int = 60) -> List[Dict[str, Any]]:
        """Return rolling in-memory bandwidth measurement records."""
        with self._lock:
            history_list = list(self._history)
            if limit and limit < len(history_list):
                return history_list[-limit:]
            return history_list


bandwidth_monitor = BandwidthMonitor()

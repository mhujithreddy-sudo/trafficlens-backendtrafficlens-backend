# 🔍 TrafficLens – Network Traffic Monitor (Backend)

> **Computer Networks Project-Based Learning (PBL)**  
> **Course / Academic Level:** B.Tech Computer Science & Engineering  
> **Backend Stack:** Python 3.13 • Flask • Flask-CORS • psutil • python-dotenv  

---

## 📖 1. Project Purpose

**TrafficLens** is a lightweight, educational network traffic monitoring system developed as a B.Tech Computer Networks PBL project. 

It provides real-time system network telemetry and statistics to modern web frontends (e.g., Next.js deployed on Vercel), allowing users to:
1. **Track Network Bandwidth Usage**: Measure real-time upload and download speeds and cumulative transferred data.
2. **Interface Traffic Accounting**: View hardware network interfaces (Wi-Fi, Ethernet, Loopback) with active byte statistics.
3. **Inspect Services & Protocols**: Identify active TCP and UDP sockets, protocol distribution, and associated processes (e.g., browsers, background services).
4. **Bandwidth History**: Maintain an in-memory rolling time-series buffer of bandwidth metrics for live charting without requiring database overhead.

---

## 🏛️ 2. Architecture & Design

```
+--------------------------------------------------------------------------+
|                     TrafficLens Architecture                             |
+--------------------------------------------------------------------------+

      [ Frontend Client ]  (Next.js / Vercel / HTML Dashboard)
               |
               |  HTTP GET / REST APIs (JSON)
               v
      [ Flask Web Server (Port 5000) ]
        - Flask-CORS (Cross-Origin Resource Sharing)
        - Clean JSON Error Handlers (404, 500, 400)
               |
      +--------+----------------------------+
      |                                     |
      v                                     v
 [ NetworkMonitor (Daemon Thread) ]    [ System Network Probes ]
  - Periodic psutil.net_io_counters()   - psutil.net_if_addrs() (IP / MAC)
  - Delta speed calculations (B/s)      - psutil.net_if_stats() (Status)
  - In-memory deque (50-100 records)    - psutil.net_connections() (Sockets)
                                        - Local ARP cache parser (Subnet)
```

### Key Architectural Decisions:
- **No Database Overhead**: Designed cleanly for an academic PBL demonstration. The system tracks rolling metrics in an in-memory FIFO queue (`collections.deque`), avoiding heavy dependencies like PostgreSQL or Redis.
- **Thread-Safe Sampling**: A lightweight background daemon thread (`NetworkMonitor`) samples network I/O counters once every second. When API consumers query `/api/network`, they receive instantaneous speeds without request latency.
- **Dual Representation**: Numerical values (`bytes`, `speed` in B/s) are provided alongside formatted strings (e.g., `12.5 MB`, `1.20 MB/s`) for effortless frontend consumption.

---

## 🛠️ 3. Technologies

| Technology | Version | Role in Project |
| :--- | :--- | :--- |
| **Python** | 3.13+ | Core programming language |
| **Flask** | 3.1.x | Lightweight WSGI web framework and REST API routing |
| **Flask-CORS** | 6.0.x | Cross-Origin Resource Sharing handling for Vercel/localhost frontends |
| **psutil** | 7.2.x | Cross-platform retrieval of system and network utilization |
| **python-dotenv** | 1.2.x | Environment variable management via `.env` file |

---

## 📡 4. Backend REST APIs

### 1. `GET /api/health`
Checks server status and uptime.
- **Response:**
```json
{
  "status": "ok",
  "service": "TrafficLens Backend",
  "timestamp": "2026-10-11T13:26:26.470892+00:00",
  "uptime_seconds": 2.71
}
```

### 2. `GET /api/network`
Retrieves cumulative data transfer and real-time upload/download speeds.
- **Response:**
```json
{
  "status": "success",
  "timestamp": "2026-10-11T13:26:26.503548+00:00",
  "download_bytes": 553079545,
  "upload_bytes": 214790463,
  "total_bytes": 767870008,
  "download_bytes_formatted": "527.46 MB",
  "upload_bytes_formatted": "204.84 MB",
  "total_bytes_formatted": "732.30 MB",
  "download_speed": 1490.17,
  "upload_speed": 1053.19,
  "total_speed": 2543.36,
  "download_speed_formatted": "1.46 KB/s",
  "upload_speed_formatted": "1.03 KB/s",
  "total_speed_formatted": "2.48 KB/s",
  "packets_sent": 136193,
  "packets_recv": 147692
}
```

### 3. `GET /api/devices`
Lists detected network interfaces and local subnet nodes.
- **Response:**
```json
{
  "status": "success",
  "devices_count": 8,
  "devices": [
    {
      "device_name": "Wi-Fi (Local Interface)",
      "interface": "Wi-Fi",
      "device_type": "interface",
      "ip_address": "192.168.29.127",
      "mac_address": "00-72-EE-DE-63-9A",
      "status": "online",
      "download_usage": 553079545,
      "upload_usage": 214790463,
      "total_usage": 767870008,
      "download_usage_formatted": "527.46 MB",
      "upload_usage_formatted": "204.84 MB",
      "total_usage_formatted": "732.30 MB",
      "speed_mbps": 240,
      "is_local": true
    }
  ],
  "limitation_note": "Per-device bandwidth accounting across external LAN nodes requires router/gateway SNMP monitoring or promiscuous packet capture. Real hardware traffic counters are provided for local system network interfaces."
}
```

### 4. `GET /api/services`
Inspects active TCP/UDP connections and groups them by application or protocol.
- **Response:**
```json
{
  "status": "success",
  "total_connections": 113,
  "services": [
    {
      "service": "brave.exe",
      "protocol": "UDP",
      "connection_count": 23,
      "status": "ESTABLISHED",
      "local_address": "192.168.29.127:61952",
      "remote_address": "13 endpoints",
      "sample_remote": "2606:4700::443"
    }
  ],
  "connections": [
    {
      "service": "brave.exe",
      "pid": 14520,
      "protocol": "UDP",
      "local_address": "192.168.29.127:61952",
      "remote_address": "2606:4700::443",
      "status": "ESTABLISHED"
    }
  ]
}
```

### 5. `GET /api/history`
Returns rolling in-memory bandwidth usage history for live chart plotting.
- **Response:**
```json
{
  "status": "success",
  "records_count": 60,
  "history": [
    {
      "timestamp": "2026-10-11T13:26:25.845382+00:00",
      "time": "18:56:25",
      "download": 1490.17,
      "upload": 1053.19,
      "total": 2543.36,
      "download_formatted": "1.46 KB/s",
      "upload_formatted": "1.03 KB/s",
      "total_formatted": "2.48 KB/s",
      "bytes_recv_total": 553070581,
      "bytes_sent_total": 214790097
    }
  ]
}
```

---

## 🚀 5. How to Run the Backend

### Prerequisites
- Python 3.13 installed.

### Setup Steps
```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create Python virtual environment
python -m venv venv

# 3. Activate the virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
.\venv\Scripts\activate.bat
# Linux / macOS:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start the Flask server
python app.py
```

The server will start at:
```
http://127.0.0.1:5000
```

### Running Test Suites
```bash
# Automated endpoint and CORS verification
python test_app.py

# Live TCP server test
python test_live_http.py
```

---

## 🔗 6. How Frontend Connects to Backend

### Environment Configuration
In your Next.js or React frontend project root, configure `.env.local`:

```env
# Local development
NEXT_PUBLIC_API_URL=http://127.0.0.1:5000

# When backend is deployed (e.g. Render, Railway, AWS):
# NEXT_PUBLIC_API_URL=https://your-trafficlens-backend.onrender.com
```

### TypeScript / JavaScript Integration
Use the provided `frontend_integration/api.ts` client:
```typescript
import { api } from '@/lib/api';

// Fetch live bandwidth stats
const stats = await api.getNetwork();
console.log(`Current download speed: ${stats.download_speed_formatted}`);

// Fetch active services
const services = await api.getServices();

// Fetch bandwidth history for charts
const history = await api.getHistory();
```

---

## ⚠️ 7. Computer Networks PBL Scope & Limitations

1. **Host-Level Interface Measurement vs. LAN-Wide Accounting**:
   - `psutil` reads network I/O counters directly from the operating system's network adapter drivers (`psutil.net_io_counters(pernic=True)`).
   - This provides **100% authentic byte counters** for local machine interfaces (Wi-Fi, Ethernet).
   - Measuring traffic transferred between *other third-party devices on the same Wi-Fi router* is not physically possible from a single non-promiscuous endpoint without managed router access, SNMP traps, or ARP spoofing.
   - For educational integrity, TrafficLens clearly identifies local interface hardware statistics and flags detected LAN nodes as requiring router-level packet capture.
2. **Process Access Permissions**:
   - Active TCP/UDP connections for standard user processes are mapped accurately to process names.
   - For privileged system/kernel sockets where standard user permissions restrict process inspection, TrafficLens falls back gracefully to standard port mapping (e.g., Port 443 → HTTPS, Port 53 → DNS).
3. **No Database Requirement**:
   - The system intentionally keeps traffic history in an in-memory rolling buffer (last 60–100 seconds) to demonstrate real-time data streaming without persistent storage complexity.

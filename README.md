# 🔍 TrafficLens – Network Traffic Monitor (FastAPI Backend)

> **Computer Networks Project-Based Learning (PBL)**  
> **Degree Program:** B.Tech Computer Science & Engineering  
> **Academic Focus:** Real-time Bandwidth Telemetry • Socket Analysis • Interface Accounting • Device Discovery • Protocol & Service Classification • Flow Analytics • REST API Integration

---

## 📖 1. Project Overview

**TrafficLens** is a modular, production-quality network traffic monitoring backend built with **FastAPI**, **SQLAlchemy**, and **psutil** / **Scapy**. Designed for academic Computer Networks demonstrations and real-world system telemetry, it bridges low-level operating system network stacks directly to modern web dashboards (such as Next.js/React).

### Key Features:
- **Real-Time Bandwidth Metering:** Calculates instantaneous download and upload rates in Megabits per second (Mbps) using exact byte deltas over periodic ticks ($\Delta \text{Bytes} \times 8 / \Delta t$).
- **Hardware Interface Accounting:** Measures physical byte counters on local adapters (Wi-Fi 802.11, Ethernet 802.3, Loopback).
- **Device Discovery:** Discovers local interfaces and active LAN neighbors via ARP cache inspection and reverse DNS resolution.
- **Service & Transport Analysis:** Inspects active TCP/UDP sockets, associates them with local host processes, and classifies standard services (HTTPS, HTTP, DNS, SSH, etc.).
- **Packet Capture & Graceful Fallback:** Uses Scapy for packet metadata extraction (IPs, ports, protocols, packet sizes). If Npcap or elevated privileges are absent, falls back gracefully to socket-level telemetry without crashing.
- **Privacy & Safety:** Strictly metadata-only capture. Never logs or stores raw packet payloads, credentials, or sensitive user contents.
- **Historical Telemetry & Analytics:** Persists bandwidth, traffic, and device records in SQLite (or PostgreSQL) with rolling timeline bucketing (1h, 6h, 24h, 7d).
- **Deterministic Alerts:** Flags bandwidth spikes and rate anomalies against baseline moving averages.

---

## 🏛️ 2. Architecture & Design

```text
                  +----------------------------------------------+
                  |         TrafficLens Next.js Frontend         |
                  |             (localhost:3000 / Vercel)        |
                  +----------------------------------------------+
                                         │
                                         │ HTTP REST API (JSON) / CORS
                                         ▼
                  +----------------------------------------------+
                  |         FastAPI REST API (Port 8000)         |
                  |     - Automatic OpenAPI / Swagger Docs       |
                  |     - Pydantic Input/Output Schemas          |
                  |     - Global Error Handling & Logging        |
                  +----------------------------------------------+
                                         │
             ┌───────────────────────────┼───────────────────────────┐
             ▼                           ▼                           ▼
  +─────────────────────+     +─────────────────────+     +─────────────────────+
  |  BandwidthMonitor   |     |  DeviceDiscovery    |     |  PacketAnalyzer     |
  |  (Background Thread)|     |  (ARP / Reverse DNS)|     |  (Scapy / Sockets)  |
  |  psutil net_io      |     |  Local Interfaces   |     |  Protocol / Port    |
  +─────────────────────+     +─────────────────────+     +─────────────────────+
             │                           │                           │
             └───────────────────────────┼───────────────────────────┘
                                         ▼
                  +----------------------------------------------+
                  |             SQLAlchemy 2.0 ORM               |
                  |      SQLite (Local) / PostgreSQL (Cloud)     |
                  +----------------------------------------------+
```

---

## 💻 3. Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI (Python 3.12+ / 3.13) | Asynchronous REST API framework |
| **ASGI Server** | Uvicorn | High-performance ASGI production server |
| **System Probing** | psutil | Hardware interface telemetry, network I/O, process sockets |
| **Packet Inspection** | Scapy | Transport/Network layer packet metadata extraction |
| **ORM / Database** | SQLAlchemy | Relational persistence for bandwidth, traffic, devices, alerts |
| **Default Storage** | SQLite (`trafficlens.db`) | Zero-config local embedded storage |
| **Validation & Settings** | Pydantic & Pydantic-Settings | Request/response models and `.env` parsing |
| **Testing** | pytest & httpx | Automated integration and unit test suite |

---

## 📁 4. Project Structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, lifespan hooks, CORS & routes
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py         # DB session dependencies
│   │   └── routes/
│   │       ├── health.py           # GET /api/health
│   │       ├── network.py          # GET /api/network
│   │       ├── bandwidth.py        # GET /api/bandwidth, /api/bandwidth/history
│   │       ├── devices.py          # GET /api/devices, /api/devices/{id}
│   │       ├── services.py         # GET /api/services
│   │       ├── traffic.py          # GET /api/traffic, /api/traffic/summary
│   │       ├── analytics.py        # GET /api/analytics/*
│   │       ├── history.py          # GET /api/history/*
│   │       ├── alerts.py           # GET /api/alerts
│   │       └── settings.py         # GET/PUT /api/settings
│   ├── core/
│   │   ├── config.py               # Pydantic BaseSettings (.env loading)
│   │   ├── database.py             # SQLAlchemy engine & sessionmaker
│   │   └── logging_config.py       # Structured logging setup
│   ├── models/
│   │   ├── device.py               # Device SQLAlchemy model
│   │   ├── traffic.py              # TrafficRecord SQLAlchemy model
│   │   ├── bandwidth.py            # BandwidthRecord SQLAlchemy model
│   │   ├── service.py              # ServiceRecord SQLAlchemy model
│   │   └── alert.py                # Alert SQLAlchemy model
│   ├── schemas/                    # Pydantic validation & response schemas
│   │   ├── device.py
│   │   ├── traffic.py
│   │   ├── bandwidth.py
│   │   ├── service.py
│   │   ├── analytics.py
│   │   └── settings.py
│   ├── services/                   # Modular background worker services
│   │   ├── bandwidth_monitor.py
│   │   ├── network_monitor.py
│   │   ├── device_discovery.py
│   │   ├── packet_analyzer.py
│   │   ├── service_analyzer.py
│   │   ├── analytics_service.py
│   │   └── history_service.py
│   └── utils/
│       ├── network_utils.py        # Byte formatters, IP helpers
│       ├── protocol_utils.py       # Port & protocol classification
│       └── system_utils.py         # OS & driver capability detection
├── tests/                          # Automated test suite (19 tests)
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_network.py
│   ├── test_bandwidth.py
│   ├── test_devices.py
│   ├── test_services.py
│   ├── test_traffic.py
│   ├── test_analytics.py
│   └── test_settings.py
├── .env.example
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── run.py                          # Application entry point
```

---

## 🚀 5. Installation & Local Setup

### Step 1: Create Virtual Environment
```powershell
# Navigate to backend directory
cd "C:\Users\M.Hujith Reddy\.gemini\antigravity\scratch\trafficlens\backend"

# Create virtual environment with Python 3.12+ or 3.13
python -m venv venv

# Activate virtual environment on Windows
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Default configuration (`.env`):
```env
APP_NAME=TrafficLens
APP_ENV=development
DEBUG=true

HOST=0.0.0.0
PORT=8000

DATABASE_URL=sqlite:///./trafficlens.db
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173

MONITORING_MODE=real
PACKET_CAPTURE_ENABLED=true
SAMPLE_INTERVAL_SECONDS=1.0
HISTORY_RETENTION_HOURS=24
BANDWIDTH_ALERT_THRESHOLD_MBPS=50.0
TRAFFIC_LEVEL_LOW_MBPS=5.0
TRAFFIC_LEVEL_MEDIUM_MBPS=25.0
```

### Step 4: Run the Server
```powershell
python run.py
# or:
uvicorn app.main:app --reload --port 8000
```
> Server will start listening at: `http://localhost:8000`

---

## 📡 6. REST API Endpoints Contract

All endpoints return structured JSON with standard HTTP status codes:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service vitality, database connectivity, monitoring status |
| `GET` | `/api/network` | Host adapters, local IP, gateway, cumulative I/O counters |
| `GET` | `/api/bandwidth` | Instantaneous transfer speeds (`download_mbps`, `upload_mbps`) |
| `GET` | `/api/bandwidth/history` | Historical bandwidth measurements (`hours`, `limit` params) |
| `GET` | `/api/devices` | Discovered network adapters and observable LAN neighbors |
| `GET` | `/api/devices/{id}` | Specific device details, byte totals, and recent traffic flows |
| `GET` | `/api/devices/{id}/traffic`| Recent traffic flows for a device |
| `GET` | `/api/services` | Active transport sockets, process mapping, and services |
| `GET` | `/api/traffic` | Recent packet flow records (`protocol`, `limit`, `source_ip`) |
| `GET` | `/api/traffic/summary` | Protocol distribution (TCP/UDP/ICMP) & top communicators |
| `GET` | `/api/analytics/overview` | Dashboard telemetry, active device counts, traffic levels |
| `GET` | `/api/analytics/top-devices` | Devices ranked by total traffic consumed |
| `GET` | `/api/analytics/top-services`| Services ranked by traffic share with exact percentages |
| `GET` | `/api/analytics/timeline` | Time-series chart points (`range=1h,6h,24h,7d`) |
| `GET` | `/api/alerts` | Network anomaly alerts (traffic spikes, bandwidth threshold) |
| `GET` | `/api/history/traffic` | Historical traffic records with date filters |
| `GET` | `/api/history/bandwidth` | Historical bandwidth records |
| `GET` | `/api/history/devices` | Historical device observations |
| `GET` | `/api/history` | Rolling bandwidth series (Next.js frontend compatible) |
| `GET` | `/api/settings` | Current runtime monitoring configuration |
| `PUT` | `/api/settings` | Update runtime alert thresholds and sample intervals |

Interactive Swagger documentation is available at:
`http://localhost:8000/docs`
Raw OpenAPI schema is available at:
`http://localhost:8000/openapi.json`

---

## 🧪 7. Running Automated Tests

Run the full pytest suite:
```powershell
pytest tests -v
```
All 19 test cases verify:
- Health and database connection checks
- Network adapter statistics
- Bandwidth rate calculation and Mbps conversion
- Device discovery and 404 error handling
- Service and socket inspection
- Traffic summary and protocol distribution
- Analytics overview and top consumers ranking
- Dynamic settings updates and alert queries

---

## 🛡️ 8. Windows & Packet Capture Notes

1. **Npcap Requirement:**
   - Raw packet capture via Scapy on Windows requires the free [Npcap driver](https://npcap.com/) installed with "WinPcap API-compatible Mode" enabled.
2. **Graceful Fallback:**
   - If Npcap or elevated Administrator privileges are not available, **TrafficLens does NOT crash**.
   - It gracefully falls back to system connection socket inspection (`psutil.net_connections`) and physical interface accounting (`psutil.net_io_counters`), clearly reporting `"packet_capture_available": false` in `/api/traffic/summary` while continuing to stream live data.
3. **No Fake Data Guarantee:**
   - When packet capture is in fallback mode, zero fake packets are generated. Real TCP/UDP sockets currently open on the operating system are observed.

---

## 🔌 9. Connecting to the Next.js Frontend

To connect your existing Vercel Next.js frontend (`TrafficLens UI design`), set:

In `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```
When hosting the backend in production (e.g. Render, Railway, AWS EC2):
```env
NEXT_PUBLIC_API_URL=https://<your-backend-domain>
```
All endpoints and response schemas maintain 100% backward compatibility with the existing frontend client!

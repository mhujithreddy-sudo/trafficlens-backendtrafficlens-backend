import urllib.request
import json

base_url = "http://127.0.0.1:5000"

endpoints = [
    "/api/health",
    "/api/network",
    "/api/devices",
    "/api/services",
    "/api/history"
]

print("=== Testing Live Server over TCP at http://127.0.0.1:5000 ===")
for ep in endpoints:
    url = f"{base_url}{ep}"
    req = urllib.request.Request(url, headers={"Origin": "https://trafficlens-frontend.vercel.app"})
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            cors = resp.headers.get("Access-Control-Allow-Origin")
            data = json.loads(resp.read().decode())
            print(f"\n[OK] {ep} -> Status: {status}, CORS: {cors}")
            if ep == "/api/health":
                print(f"     Status: {data.get('status')}, Service: {data.get('service')}")
            elif ep == "/api/network":
                print(f"     Download Speed: {data.get('download_speed_formatted')}, Upload Speed: {data.get('upload_speed_formatted')}")
                print(f"     Total Bytes: {data.get('total_bytes_formatted')}")
            elif ep == "/api/devices":
                print(f"     Devices count: {data.get('devices_count')}")
                if data.get("devices"):
                    first = data["devices"][0]
                    print(f"     Top device: {first.get('device_name')} - Usage: {first.get('total_usage_formatted')}")
            elif ep == "/api/services":
                print(f"     Total connections: {data.get('total_connections')}, Services count: {len(data.get('services', []))}")
                if data.get("services"):
                    first = data["services"][0]
                    print(f"     Top service: {first.get('service')} ({first.get('protocol')}) - {first.get('connection_count')} connections")
            elif ep == "/api/history":
                print(f"     History records: {data.get('records_count')}")
    except Exception as e:
        print(f"[ERROR] {ep}: {e}")

print("\n=== Live HTTP Testing Completed Successfully! ===")

import time
import json
from app import app, network_monitor

def run_tests():
    print("========================================")
    print(" TrafficLens Backend Test Suite ")
    print("========================================")
    
    client = app.test_client()
    
    # Wait 2 seconds for monitor to gather samples
    print("[1/6] Waiting for NetworkMonitor sampler to collect initial ticks...")
    time.sleep(2.5)
    
    # 1. Health
    print("\n--- Testing GET /api/health ---")
    res = client.get("/api/health")
    print(f"Status: {res.status_code}")
    data = res.get_json()
    print(f"Response: {json.dumps(data, indent=2)}")
    assert res.status_code == 200, "Health check failed"
    assert data.get("status") == "ok", "Health status != ok"
    assert "service" in data, "Service name missing"
    
    # 2. Network
    print("\n--- Testing GET /api/network ---")
    res = client.get("/api/network")
    print(f"Status: {res.status_code}")
    data = res.get_json()
    print(f"Response: {json.dumps(data, indent=2)}")
    assert res.status_code == 200, "Network stats failed"
    assert "download_bytes" in data, "download_bytes missing"
    assert "upload_bytes" in data, "upload_bytes missing"
    assert "total_bytes" in data, "total_bytes missing"
    assert "download_speed" in data, "download_speed missing"
    assert "upload_speed" in data, "upload_speed missing"
    assert "timestamp" in data, "timestamp missing"
    
    # 3. Devices
    print("\n--- Testing GET /api/devices ---")
    res = client.get("/api/devices")
    print(f"Status: {res.status_code}")
    data = res.get_json()
    print(f"Devices count: {data.get('devices_count')}")
    sample_dev = data.get("devices", [])[:2]
    print(f"Sample devices: {json.dumps(sample_dev, indent=2)}")
    assert res.status_code == 200, "Devices endpoint failed"
    assert "devices" in data, "devices key missing"
    assert len(data["devices"]) > 0, "No devices or interfaces detected"
    
    # 4. Services
    print("\n--- Testing GET /api/services ---")
    res = client.get("/api/services")
    print(f"Status: {res.status_code}")
    data = res.get_json()
    print(f"Total connections: {data.get('total_connections')}")
    sample_srv = data.get("services", [])[:3]
    print(f"Top services: {json.dumps(sample_srv, indent=2)}")
    assert res.status_code == 200, "Services endpoint failed"
    assert "services" in data, "services key missing"
    assert "connections" in data, "connections key missing"
    
    # 5. History
    print("\n--- Testing GET /api/history ---")
    res = client.get("/api/history")
    print(f"Status: {res.status_code}")
    data = res.get_json()
    print(f"Records count: {data.get('records_count')}")
    sample_hist = data.get("history", [])[-3:]
    print(f"Recent history samples: {json.dumps(sample_hist, indent=2)}")
    assert res.status_code == 200, "History endpoint failed"
    assert "history" in data, "history key missing"
    assert len(data["history"]) > 0, "History records empty"
    
    # 6. CORS Verification
    print("\n--- Testing CORS headers ---")
    res = client.get("/api/health", headers={"Origin": "https://trafficlens.vercel.app"})
    cors_header = res.headers.get("Access-Control-Allow-Origin")
    print(f"Access-Control-Allow-Origin: {cors_header}")
    assert cors_header is not None, "CORS header missing!"
    
    # 7. Error Handling (404)
    print("\n--- Testing Error Handling (404) ---")
    res = client.get("/api/unknown_endpoint")
    print(f"Status: {res.status_code}")
    data = res.get_json()
    print(f"404 Response: {json.dumps(data, indent=2)}")
    assert res.status_code == 404, "Expected 404 status code"
    assert "error" in data, "Expected error key in JSON"
    
    print("\n========================================")
    print(" ALL TESTS PASSED SUCCESSFULLY! ")
    print("========================================")

if __name__ == "__main__":
    run_tests()

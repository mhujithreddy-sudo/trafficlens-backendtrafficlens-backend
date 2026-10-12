"""
Tests for settings, alerts, and history endpoints.
"""


def test_get_settings(client):
    """Test GET /api/settings returns valid configuration."""
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "TrafficLens"
    assert "packet_capture_enabled" in data
    assert "sample_interval_seconds" in data
    assert "traffic_level_low_mbps" in data


def test_update_settings(client):
    """Test PUT /api/settings modifies runtime thresholds."""
    payload = {
        "sample_interval_seconds": 2.0,
        "traffic_level_low_mbps": 8.0,
    }
    response = client.put("/api/settings", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sample_interval_seconds"] == 2.0
    assert data["traffic_level_low_mbps"] == 8.0


def test_alerts_endpoint(client):
    """Test GET /api/alerts returns alerts list."""
    response = client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "alerts_count" in data
    assert isinstance(data["alerts"], list)


def test_history_endpoints(client):
    """Test GET /api/history and specific history endpoints."""
    # Base rolling history
    res1 = client.get("/api/history?limit=10")
    assert res1.status_code == 200
    assert "history" in res1.json()

    # Bandwidth history
    res2 = client.get("/api/history/bandwidth?limit=10")
    assert res2.status_code == 200
    assert "records" in res2.json()

    # Traffic history
    res3 = client.get("/api/history/traffic?limit=10")
    assert res3.status_code == 200
    assert "records" in res3.json()

    # Devices history
    res4 = client.get("/api/history/devices?limit=10")
    assert res4.status_code == 200
    assert "records" in res4.json()

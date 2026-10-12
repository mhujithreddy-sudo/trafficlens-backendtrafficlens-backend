"""
Tests for analytics overview, top consumers, and chart timelines.
"""


def test_analytics_overview(client):
    """Test GET /api/analytics/overview returns dashboard counters."""
    response = client.get("/api/analytics/overview")
    assert response.status_code == 200
    data = response.json()
    assert "total_bandwidth" in data
    assert "download_bytes" in data
    assert "upload_bytes" in data
    assert "active_devices" in data
    assert "current_download_mbps" in data
    assert "traffic_level" in data
    assert data["traffic_level"] in ("LOW", "MEDIUM", "HIGH")
    assert data["network_load"] in ("Normal", "Moderate", "Heavy")


def test_analytics_top_devices(client):
    """Test GET /api/analytics/top-devices returns ranked devices."""
    response = client.get("/api/analytics/top-devices?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_analytics_top_services(client):
    """Test GET /api/analytics/top-services returns ranked services with percentages."""
    response = client.get("/api/analytics/top-services?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_analytics_timeline(client):
    """Test GET /api/analytics/timeline returns time-series chart data."""
    response = client.get("/api/analytics/timeline?range=1h")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["range"] == "1h"
    assert "points" in data
    assert isinstance(data["points"], list)

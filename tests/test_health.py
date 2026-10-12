"""
Tests for health check and root endpoints.
"""


def test_root_endpoint(client):
    """Test GET / returns welcome JSON and documentation links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "TrafficLens" in data["service"]
    assert "/docs" in data["docs"]


def test_health_endpoint(client):
    """Test GET /api/health verifies database and monitoring status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("online", "degraded")
    assert data["service"] == "TrafficLens Backend"
    assert "version" in data
    assert "database" in data
    assert "monitoring" in data
    assert "uptime_seconds" in data

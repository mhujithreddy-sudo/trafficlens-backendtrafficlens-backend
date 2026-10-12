"""
Tests for service identification and socket mapping.
"""


def test_services_endpoint(client):
    """Test GET /api/services returns active services and connection details."""
    response = client.get("/api/services")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "total_connections" in data
    assert "services" in data
    assert isinstance(data["services"], list)

"""
Tests for network information endpoint.
"""


def test_network_endpoint(client):
    """Test GET /api/network returns adapter telemetry and byte counters."""
    response = client.get("/api/network")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "hostname" in data
    assert "local_ip" in data
    assert "interfaces" in data
    assert isinstance(data["interfaces"], list)
    assert "download_bytes" in data
    assert "upload_bytes" in data
    assert "download_speed" in data
    assert "upload_speed" in data

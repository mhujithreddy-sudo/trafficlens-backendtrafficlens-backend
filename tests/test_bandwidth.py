"""
Tests for bandwidth monitoring and historical rate calculation.
"""


def test_bandwidth_current(client):
    """Test GET /api/bandwidth returns calculated rates and accurate Mbps values."""
    response = client.get("/api/bandwidth")
    assert response.status_code == 200
    data = response.json()
    assert "download_mbps" in data
    assert "upload_mbps" in data
    assert "total_mbps" in data
    assert "download_speed_formatted" in data
    assert "upload_speed_formatted" in data
    assert data["traffic_level"] in ("LOW", "MEDIUM", "HIGH")


def test_bandwidth_history(client):
    """Test GET /api/bandwidth/history returns list of samples."""
    response = client.get("/api/bandwidth/history?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "records_count" in data
    assert isinstance(data["history"], list)

"""
Tests for packet traffic analysis and summary endpoints.
"""


def test_traffic_list(client):
    """Test GET /api/traffic returns recent flows and capture capability flag."""
    response = client.get("/api/traffic?limit=25")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "total_count" in data
    assert "records" in data
    assert "packet_capture_active" in data
    assert isinstance(data["records"], list)


def test_traffic_summary(client):
    """Test GET /api/traffic/summary returns protocol metrics and top talkers."""
    response = client.get("/api/traffic/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "total_packets" in data
    assert "total_bytes" in data
    assert "tcp_packets" in data
    assert "udp_packets" in data
    assert "top_source_ips" in data
    assert "top_destination_ips" in data
    assert "top_ports" in data

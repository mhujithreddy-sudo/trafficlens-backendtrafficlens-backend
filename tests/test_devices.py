"""
Tests for device discovery and per-device traffic inspection.
"""


def test_devices_list(client):
    """Test GET /api/devices lists local adapters and LAN neighbors."""
    response = client.get("/api/devices")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "devices_count" in data
    assert "devices" in data
    assert isinstance(data["devices"], list)
    assert len(data["devices"]) > 0

    # Validate first device structure
    dev = data["devices"][0]
    assert "device_name" in dev
    assert "ip_address" in dev
    assert "device_type" in dev
    assert "download_usage_formatted" in dev


def test_device_detail_not_found(client):
    """Test GET /api/devices/99999 returns 404 for non-existent device."""
    response = client.get("/api/devices/99999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data or "error" in data


def test_device_detail_existing(client):
    """Test GET /api/devices/{id} for existing device."""
    list_res = client.get("/api/devices")
    devices = list_res.json()["devices"]
    if devices and devices[0].get("id"):
        dev_id = devices[0]["id"]
        detail_res = client.get(f"/api/devices/{dev_id}")
        assert detail_res.status_code == 200
        assert "device" in detail_res.json()

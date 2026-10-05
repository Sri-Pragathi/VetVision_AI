"""Tests for health check endpoint."""


def test_health_endpoint(client):
    """Verify GET /api/v1/health returns success and expected message."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    assert json_data["message"] == "VetVision AI backend is running"

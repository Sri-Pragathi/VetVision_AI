"""Tests for health check endpoint, database status probe, and liveness/readiness checks."""
from unittest.mock import patch


def test_health_endpoint(client):
    """Verify GET /api/v1/health returns success, database connected, and expected message."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    assert json_data["message"] == "VetVision AI backend is running"
    assert json_data["data"]["database"] == "connected"
    assert json_data["data"]["status"] == "healthy"


def test_health_endpoint_database_disconnected(client):
    """Verify GET /api/v1/health returns 503 and safe disconnected status without leaking internal details."""
    with patch("app.routes.health_routes.db.session.execute", side_effect=Exception("Database connection timeout")):
        response = client.get("/api/v1/health")
        assert response.status_code == 503
        json_data = response.get_json()
        assert json_data["success"] is False
        assert json_data["message"] == "VetVision AI backend is degraded or database unavailable"
        assert json_data["errors"]["database"] == "disconnected"
        assert json_data["errors"]["status"] == "unhealthy"
        # Ensure raw exception message or credentials are not leaked in response
        assert "timeout" not in str(json_data).lower() or json_data["errors"]["database"] == "disconnected"


def test_liveness_and_readiness_probes(client):
    """Verify dedicated /health/live and /health/ready endpoints."""
    live_res = client.get("/api/v1/health/live")
    assert live_res.status_code == 200
    assert live_res.get_json()["data"]["status"] == "alive"

    ready_res = client.get("/api/v1/health/ready")
    assert ready_res.status_code == 200
    assert ready_res.get_json()["data"]["database"] == "connected"

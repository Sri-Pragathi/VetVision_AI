"""Tests for user profile endpoints."""


def test_get_current_user_profile(client, registered_user):
    """Verify GET /api/v1/users/me returns authenticated user's profile."""
    response = client.get("/api/v1/users/me", headers=registered_user["headers"])
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["email"] == registered_user["payload"]["email"]
    assert data["data"]["name"] == registered_user["payload"]["name"]


def test_update_current_user_profile(client, registered_user):
    """Verify PUT /api/v1/users/me updates name and email successfully."""
    update_payload = {
        "name": "Dr. John Updated",
    }
    response = client.put(
        "/api/v1/users/me",
        headers=registered_user["headers"],
        json=update_payload,
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["name"] == "Dr. John Updated"


def test_update_email_conflict(client, registered_user, second_user):
    """Verify updating email to one that already exists causes 409 Conflict."""
    update_payload = {
        "email": second_user["payload"]["email"],
    }
    response = client.put(
        "/api/v1/users/me",
        headers=registered_user["headers"],
        json=update_payload,
    )
    assert response.status_code == 409
    data = response.get_json()
    assert data["success"] is False
    assert "already exists" in data["message"]

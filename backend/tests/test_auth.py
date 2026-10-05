"""Tests for authentication and authorization flows."""


def test_successful_registration(client):
    """Verify new user registration creates user and returns tokens."""
    payload = {
        "name": "Dr. Sarah Connor",
        "email": "sarah.connor@example.com",
        "password": "SecurePassword123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert "tokens" in data["data"]
    assert "access_token" in data["data"]["tokens"]
    assert "refresh_token" in data["data"]["tokens"]
    assert data["data"]["user"]["email"] == "sarah.connor@example.com"
    assert "password_hash" not in data["data"]["user"]


def test_duplicate_registration(client, registered_user):
    """Verify registering with an existing email returns 409 Conflict."""
    payload = {
        "name": "Another Name",
        "email": registered_user["payload"]["email"],
        "password": "Password999!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    data = response.get_json()
    assert data["success"] is False
    assert "already exists" in data["message"]


def test_registration_validation_errors(client):
    """Verify input validation fails gracefully for bad inputs."""
    # Bad email
    res1 = client.post("/api/v1/auth/register", json={
        "name": "Test User",
        "email": "invalid-email-format",
        "password": "ValidPassword123!",
    })
    assert res1.status_code == 422
    assert res1.get_json()["success"] is False

    # Weak password (< 8 chars)
    res2 = client.post("/api/v1/auth/register", json={
        "name": "Test User",
        "email": "valid@email.com",
        "password": "short",
    })
    assert res2.status_code == 422
    assert res2.get_json()["success"] is False


def test_successful_login(client, registered_user):
    """Verify authenticating with correct credentials returns tokens."""
    payload = {
        "email": registered_user["payload"]["email"],
        "password": registered_user["payload"]["password"],
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "access_token" in data["data"]["tokens"]


def test_invalid_login_credentials(client, registered_user):
    """Verify incorrect password returns 401 Unauthorized."""
    payload = {
        "email": registered_user["payload"]["email"],
        "password": "WrongPassword999!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False


def test_protected_endpoint_without_token(client):
    """Verify accessing protected endpoint without token returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False


def test_auth_me_with_valid_token(client, registered_user):
    """Verify GET /api/v1/auth/me returns current user info."""
    response = client.get("/api/v1/auth/me", headers=registered_user["headers"])
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["email"] == registered_user["payload"]["email"]


def test_refresh_token_flow(client, registered_user):
    """Verify POST /api/v1/auth/refresh issues a new access token."""
    refresh_header = {
        "Authorization": f"Bearer {registered_user['refresh_token']}"
    }
    response = client.post("/api/v1/auth/refresh", headers=refresh_header)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "access_token" in data["data"]


def test_logout_revokes_token(client, registered_user):
    """Verify logging out adds token to blocklist and revokes subsequent access."""
    # Logout using current access token
    logout_res = client.post("/api/v1/auth/logout", headers=registered_user["headers"])
    assert logout_res.status_code == 200
    assert logout_res.get_json()["success"] is True

    # Try accessing protected endpoint with the revoked token
    me_res = client.get("/api/v1/auth/me", headers=registered_user["headers"])
    assert me_res.status_code == 401
    assert "revoked" in me_res.get_json()["message"].lower()

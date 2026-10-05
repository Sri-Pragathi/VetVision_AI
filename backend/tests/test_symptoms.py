"""Tests for symptom vocabulary endpoints."""


def test_list_all_symptoms(client):
    """Verify GET /api/v1/symptoms returns seeded vocabulary."""
    response = client.get("/api/v1/symptoms")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    symptoms = data["data"]
    assert len(symptoms) >= 20
    names = [s["name"] for s in symptoms]
    assert "vomiting" in names
    assert "coughing" in names
    assert "itching" in names
    assert "difficulty breathing" in names


def test_filter_symptoms_by_category(client):
    """Verify filtering symptoms by category works as expected."""
    response = client.get("/api/v1/symptoms?category=Skin")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) >= 4
    for sym in data:
        assert sym["category"] == "Skin"


def test_filter_symptoms_case_insensitive(client):
    """Verify category filtering is case-insensitive."""
    response = client.get("/api/v1/symptoms?category=respiratory")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) >= 3
    for sym in data:
        assert sym["category"] == "Respiratory"


def test_filter_symptoms_non_existent_category(client):
    """Verify filtering with unknown category returns empty list."""
    response = client.get("/api/v1/symptoms?category=NonExistentCategory")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == 0

"""Pytest fixtures for VetVision AI backend tests."""
import pytest
from app import create_app
from app.extensions import db
from app.models.symptom import seed_symptoms


@pytest.fixture(scope="session")
def app():
    """Create application configured for testing."""
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Test client per test with clean database and seeded symptoms."""
    with app.test_client() as test_client:
        with app.app_context():
            # Clean up db state between tests
            db.session.rollback()
            for table in reversed(db.metadata.sorted_tables):
                db.session.execute(table.delete())
            db.session.commit()
            # Seed standard symptom vocabulary
            seed_symptoms()
        yield test_client


@pytest.fixture
def registered_user(client):
    """Register a default test user and return credentials and tokens."""
    payload = {
        "name": "Dr. John Doe",
        "email": "john.doe@vetvision.ai",
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    data = response.get_json()["data"]
    return {
        "payload": payload,
        "user": data["user"],
        "tokens": data["tokens"],
        "access_token": data["tokens"]["access_token"],
        "refresh_token": data["tokens"]["refresh_token"],
        "headers": {"Authorization": f"Bearer {data['tokens']['access_token']}"},
    }


@pytest.fixture
def second_user(client):
    """Register a second distinct test user for multi-tenant isolation tests."""
    payload = {
        "name": "Jane Smith",
        "email": "jane.smith@vetvision.ai",
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    data = response.get_json()["data"]
    return {
        "payload": payload,
        "user": data["user"],
        "tokens": data["tokens"],
        "access_token": data["tokens"]["access_token"],
        "refresh_token": data["tokens"]["refresh_token"],
        "headers": {"Authorization": f"Bearer {data['tokens']['access_token']}"},
    }


@pytest.fixture
def test_pet(client, registered_user):
    """Create a test pet owned by registered_user."""
    pet_payload = {
        "name": "Max",
        "species": "Canine",
        "breed": "German Shepherd",
        "sex": "Male Neutered",
        "date_of_birth": "2020-01-15",
        "weight": 34.0,
        "allergies": "Chicken",
        "existing_conditions": "Hip dysplasia",
        "current_medications": "Glucosamine",
        "vaccination_status": "Up to date",
    }
    res = client.post("/api/v1/pets", headers=registered_user["headers"], json=pet_payload)
    return res.get_json()["data"]


@pytest.fixture
def second_user_pet(client, second_user):
    """Create a test pet owned by second_user."""
    pet_payload = {
        "name": "Mimi",
        "species": "Feline",
        "breed": "Siamese",
        "sex": "Female",
        "date_of_birth": "2021-05-10",
        "weight": 4.2,
    }
    res = client.post("/api/v1/pets", headers=second_user["headers"], json=pet_payload)
    return res.get_json()["data"]


@pytest.fixture
def test_assessment(client, registered_user, test_pet):
    """Create a health assessment session for test_pet."""
    res = client.post(
        f"/api/v1/pets/{test_pet['id']}/assessments",
        headers=registered_user["headers"],
    )
    return res.get_json()["data"]

"""Tests for pet management endpoints and multi-user security isolation."""


def test_create_pet_successful(client, registered_user):
    """Verify creating a pet with complete details returns 201 Created."""
    pet_payload = {
        "name": "Bella",
        "species": "Canine",
        "breed": "Golden Retriever",
        "sex": "Female",
        "date_of_birth": "2021-04-15",
        "weight": 28.5,
        "allergies": "Chicken protein",
        "existing_conditions": "None",
        "current_medications": "Heartworm preventative",
        "vaccination_status": "Up to date",
    }
    response = client.post(
        "/api/v1/pets",
        headers=registered_user["headers"],
        json=pet_payload,
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["name"] == "Bella"
    assert data["data"]["owner_id"] == registered_user["user"]["id"]
    assert data["data"]["species"] == "Canine"
    assert data["data"]["weight"] == 28.5
    assert data["data"]["age"] is not None


def test_create_pet_validation_failure(client, registered_user):
    """Verify pet creation fails without required fields."""
    # Missing species
    response = client.post(
        "/api/v1/pets",
        headers=registered_user["headers"],
        json={"name": "Max"},
    )
    assert response.status_code == 422
    assert response.get_json()["success"] is False


def test_retrieve_pets_user_isolation(client, registered_user, second_user):
    """Verify GET /api/v1/pets returns ONLY the authenticated user's pets."""
    # User 1 adds a dog
    client.post(
        "/api/v1/pets",
        headers=registered_user["headers"],
        json={"name": "Luna", "species": "Cat"},
    )

    # User 2 adds a cat
    client.post(
        "/api/v1/pets",
        headers=second_user["headers"],
        json={"name": "Rocky", "species": "Dog"},
    )

    # User 1 retrieves their pets
    res1 = client.get("/api/v1/pets", headers=registered_user["headers"])
    assert res1.status_code == 200
    pets1 = res1.get_json()["data"]
    assert len(pets1) == 1
    assert pets1[0]["name"] == "Luna"

    # User 2 retrieves their pets
    res2 = client.get("/api/v1/pets", headers=second_user["headers"])
    assert res2.status_code == 200
    pets2 = res2.get_json()["data"]
    assert len(pets2) == 1
    assert pets2[0]["name"] == "Rocky"


def test_unauthorized_access_to_another_users_pet(client, registered_user, second_user):
    """CRITICAL SECURITY TEST: Ensure a user CANNOT view another user's pet."""
    # User 1 creates a pet
    create_res = client.post(
        "/api/v1/pets",
        headers=registered_user["headers"],
        json={"name": "Milo", "species": "Dog"},
    )
    pet_id = create_res.get_json()["data"]["id"]

    # User 2 attempts to view User 1's pet
    hack_attempt = client.get(
        f"/api/v1/pets/{pet_id}",
        headers=second_user["headers"],
    )
    assert hack_attempt.status_code == 403
    data = hack_attempt.get_json()
    assert data["success"] is False
    assert "permission" in data["message"].lower()


def test_unauthorized_update_to_another_users_pet(client, registered_user, second_user):
    """CRITICAL SECURITY TEST: Ensure a user CANNOT modify another user's pet."""
    create_res = client.post(
        "/api/v1/pets",
        headers=registered_user["headers"],
        json={"name": "Charlie", "species": "Parrot"},
    )
    pet_id = create_res.get_json()["data"]["id"]

    # User 2 attempts to rename User 1's pet
    hack_attempt = client.put(
        f"/api/v1/pets/{pet_id}",
        headers=second_user["headers"],
        json={"name": "HackedPet"},
    )
    assert hack_attempt.status_code == 403
    assert hack_attempt.get_json()["success"] is False


def test_unauthorized_deletion_of_another_users_pet(client, registered_user, second_user):
    """CRITICAL SECURITY TEST: Ensure a user CANNOT delete another user's pet."""
    create_res = client.post(
        "/api/v1/pets",
        headers=registered_user["headers"],
        json={"name": "Oliver", "species": "Cat"},
    )
    pet_id = create_res.get_json()["data"]["id"]

    # User 2 attempts to delete User 1's pet
    hack_attempt = client.delete(
        f"/api/v1/pets/{pet_id}",
        headers=second_user["headers"],
    )
    assert hack_attempt.status_code == 403
    assert hack_attempt.get_json()["success"] is False


def test_update_own_pet(client, registered_user):
    """Verify owner can successfully update their pet details."""
    create_res = client.post(
        "/api/v1/pets",
        headers=registered_user["headers"],
        json={"name": "Cooper", "species": "Dog", "weight": 15.0},
    )
    pet_id = create_res.get_json()["data"]["id"]

    update_res = client.put(
        f"/api/v1/pets/{pet_id}",
        headers=registered_user["headers"],
        json={"weight": 16.5, "vaccination_status": "Up to date"},
    )
    assert update_res.status_code == 200
    data = update_res.get_json()["data"]
    assert data["weight"] == 16.5
    assert data["vaccination_status"] == "Up to date"


def test_delete_own_pet(client, registered_user):
    """Verify owner can successfully delete their pet."""
    create_res = client.post(
        "/api/v1/pets",
        headers=registered_user["headers"],
        json={"name": "Bailey", "species": "Rabbit"},
    )
    pet_id = create_res.get_json()["data"]["id"]

    delete_res = client.delete(
        f"/api/v1/pets/{pet_id}",
        headers=registered_user["headers"],
    )
    assert delete_res.status_code == 200

    # Ensure pet is gone
    get_res = client.get(
        f"/api/v1/pets/{pet_id}",
        headers=registered_user["headers"],
    )
    assert get_res.status_code == 404


def test_create_and_update_pet_with_enhanced_profile_fields(client, registered_user):
    """Verify pet creation and updates with medical history, weight unit, photo URL, and notes."""
    payload = {
        "name": "Max",
        "species": "Dog",
        "breed": "Golden Retriever",
        "sex": "Male",
        "weight": 32.4,
        "weight_unit": "kg",
        "photo_url": "https://example.com/photos/max.jpg",
        "spayed_neutered": True,
        "vaccination_status": "Up to date",
        "vaccination_history": "Rabies (2025), DHPP (2025), Bordetella (2026)",
        "medical_history": "Cruciate ligament repair (2024), ear infection resolved (2025)",
        "notes": "Loves tennis balls, nervous around thunderstorms.",
    }
    create_res = client.post(
        "/api/v1/pets",
        headers=registered_user["headers"],
        json=payload,
    )
    assert create_res.status_code == 201
    data = create_res.get_json()["data"]
    assert data["name"] == "Max"
    assert data["weight_unit"] == "kg"
    assert data["photo_url"] == "https://example.com/photos/max.jpg"
    assert data["spayed_neutered"] is True
    assert "Rabies" in data["vaccination_history"]
    assert "Cruciate" in data["medical_history"]
    assert "tennis balls" in data["notes"]

    pet_id = data["id"]

    # Update medical history and notes
    update_res = client.put(
        f"/api/v1/pets/{pet_id}",
        headers=registered_user["headers"],
        json={
            "weight": 72.0,
            "weight_unit": "lbs",
            "notes": "Updated: now taking joint supplements daily.",
        },
    )
    assert update_res.status_code == 200
    up_data = update_res.get_json()["data"]
    assert up_data["weight"] == 72.0
    assert up_data["weight_unit"] == "lbs"
    assert "joint supplements" in up_data["notes"]
    assert up_data["spayed_neutered"] is True


def test_multi_pet_registration_per_owner(client, registered_user):
    """Verify that a single owner can create and manage multiple distinct pet profiles."""
    pets_to_create = [
        {"name": "Milo", "species": "Dog", "breed": "Beagle"},
        {"name": "Cleo", "species": "Cat", "breed": "Siamese"},
        {"name": "Pip", "species": "Bird", "breed": "Cockatiel"},
    ]
    created_ids = []
    for pet_data in pets_to_create:
        res = client.post(
            "/api/v1/pets",
            headers=registered_user["headers"],
            json=pet_data,
        )
        assert res.status_code == 201
        created_ids.append(res.get_json()["data"]["id"])

    # List all pets
    list_res = client.get("/api/v1/pets", headers=registered_user["headers"])
    assert list_res.status_code == 200
    retrieved_pets = list_res.get_json()["data"]
    retrieved_names = [p["name"] for p in retrieved_pets]

    for expected_name in ["Milo", "Cleo", "Pip"]:
        assert expected_name in retrieved_names


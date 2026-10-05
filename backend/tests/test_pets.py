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

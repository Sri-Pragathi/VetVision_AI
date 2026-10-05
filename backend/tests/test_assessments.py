"""Comprehensive test suite for Health Assessments, Triage, and Multi-Tenant Isolation."""
from app.services.ai_data_service import AiDataPreparationService
from app.services.emergency_service import EmergencyAssessmentService


# -----------------------------------------------------------------------------
# 1. Lifecycle and CRUD
# -----------------------------------------------------------------------------

def test_create_assessment_successful(client, registered_user, test_pet):
    """1. Create assessment successfully for own pet."""
    response = client.post(
        f"/api/v1/pets/{test_pet['id']}/assessments",
        headers=registered_user["headers"],
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["pet_id"] == test_pet["id"]
    assert data["data"]["status"] == "in_progress"
    assert data["data"]["started_at"] is not None


def test_list_pet_assessments(client, registered_user, test_pet):
    """10. List assessments belonging to a pet."""
    # Create two assessments
    client.post(f"/api/v1/pets/{test_pet['id']}/assessments", headers=registered_user["headers"])
    client.post(f"/api/v1/pets/{test_pet['id']}/assessments", headers=registered_user["headers"])

    response = client.get(
        f"/api/v1/pets/{test_pet['id']}/assessments",
        headers=registered_user["headers"],
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) >= 2


def test_retrieve_assessment(client, registered_user, test_assessment):
    """2. Retrieve an assessment session."""
    response = client.get(
        f"/api/v1/assessments/{test_assessment['id']}",
        headers=registered_user["headers"],
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["id"] == test_assessment["id"]
    assert "symptoms" in data
    assert "observations" in data
    assert "notes" in data


def test_update_assessment_lifecycle(client, registered_user, test_assessment):
    """3 & 19. Update assessment status and validate lifecycle rules."""
    assessment_id = test_assessment["id"]

    # Transition in_progress -> completed
    res = client.put(
        f"/api/v1/assessments/{assessment_id}",
        headers=registered_user["headers"],
        json={"status": "completed"},
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["status"] == "completed"
    assert data["completed_at"] is not None

    # Invalid transition: completed -> in_progress should be rejected
    res_invalid = client.put(
        f"/api/v1/assessments/{assessment_id}",
        headers=registered_user["headers"],
        json={"status": "in_progress"},
    )
    assert res_invalid.status_code == 422
    assert res_invalid.get_json()["success"] is False


def test_delete_assessment(client, registered_user, test_pet):
    """4. Delete assessment successfully."""
    create_res = client.post(
        f"/api/v1/pets/{test_pet['id']}/assessments",
        headers=registered_user["headers"],
    )
    assessment_id = create_res.get_json()["data"]["id"]

    # Delete
    del_res = client.delete(
        f"/api/v1/assessments/{assessment_id}",
        headers=registered_user["headers"],
    )
    assert del_res.status_code == 200

    # Verify not found
    get_res = client.get(
        f"/api/v1/assessments/{assessment_id}",
        headers=registered_user["headers"],
    )
    assert get_res.status_code == 404


# -----------------------------------------------------------------------------
# 2. Symptoms Management
# -----------------------------------------------------------------------------

def test_add_symptom_to_assessment(client, registered_user, test_assessment):
    """5. Add a symptom to an assessment."""
    # Get a symptom ID
    sym_res = client.get("/api/v1/symptoms?category=Digestive")
    symptom_id = sym_res.get_json()["data"][0]["id"]

    payload = {
        "symptom_id": symptom_id,
        "severity": "moderate",
        "duration_value": 2.5,
        "duration_unit": "days",
        "notes": "Started after morning meal.",
    }
    response = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json=payload,
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["symptom_id"] == symptom_id
    assert data["severity"] == "moderate"
    assert data["duration_value"] == 2.5
    assert data["duration_unit"] == "days"


def test_update_assessment_symptom(client, registered_user, test_assessment):
    """6. Update symptom information on an assessment."""
    sym_res = client.get("/api/v1/symptoms?category=Respiratory")
    symptom_id = sym_res.get_json()["data"][0]["id"]

    # Add symptom first
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={
            "symptom_id": symptom_id,
            "severity": "mild",
            "duration_value": 1,
            "duration_unit": "days",
        },
    )

    # Update severity to severe and duration to 3 days
    upd_res = client.put(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms/{symptom_id}",
        headers=registered_user["headers"],
        json={
            "severity": "severe",
            "duration_value": 3,
            "notes": "Condition has worsened.",
        },
    )
    assert upd_res.status_code == 200
    data = upd_res.get_json()["data"]
    assert data["severity"] == "severe"
    assert data["duration_value"] == 3.0
    assert data["notes"] == "Condition has worsened."


def test_remove_assessment_symptom(client, registered_user, test_assessment):
    """7. Remove a symptom from an assessment."""
    sym_res = client.get("/api/v1/symptoms?category=Skin")
    symptom_id = sym_res.get_json()["data"][0]["id"]

    # Add
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={
            "symptom_id": symptom_id,
            "severity": "mild",
            "duration_value": 4,
            "duration_unit": "weeks",
        },
    )

    # Remove
    del_res = client.delete(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms/{symptom_id}",
        headers=registered_user["headers"],
    )
    assert del_res.status_code == 200

    # Ensure symptom is not in assessment anymore
    get_res = client.get(
        f"/api/v1/assessments/{test_assessment['id']}",
        headers=registered_user["headers"],
    )
    symptoms = get_res.get_json()["data"]["symptoms"]
    assert not any(s["symptom_id"] == symptom_id for s in symptoms)


# -----------------------------------------------------------------------------
# 3. Observations and Notes
# -----------------------------------------------------------------------------

def test_add_and_update_observations(client, registered_user, test_assessment):
    """8. Create and update structured observations."""
    obs_payload = {
        "appetite": "decreased",
        "water_intake": "excessive",
        "activity_level": "lethargic",
        "behaviour_change": "withdrawn",
        "sleep_change": "sleeping_more",
        "stool_change": "soft",
        "urine_change": "frequent",
        "breathing_change": "normal",
        "pain_observed": "mild_vocalizing",
    }
    response = client.put(
        f"/api/v1/assessments/{test_assessment['id']}/observations",
        headers=registered_user["headers"],
        json=obs_payload,
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["appetite"] == "decreased"
    assert data["water_intake"] == "excessive"
    assert data["activity_level"] == "lethargic"


def test_add_assessment_note(client, registered_user, test_assessment):
    """9. Add free-text clinical note."""
    response = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/notes",
        headers=registered_user["headers"],
        json={"note": "Owner reports pet ingested a small foreign object 2 days ago."},
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert "ingested a small foreign object" in data["note"]


# -----------------------------------------------------------------------------
# 4. Input Validations (422)
# -----------------------------------------------------------------------------

def test_invalid_severity_rejected(client, registered_user, test_assessment):
    """12. Validate invalid severity returns 422."""
    sym_res = client.get("/api/v1/symptoms")
    symptom_id = sym_res.get_json()["data"][0]["id"]

    response = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={
            "symptom_id": symptom_id,
            "severity": "ultra_extreme",  # Invalid
            "duration_value": 1,
            "duration_unit": "days",
        },
    )
    assert response.status_code == 422
    assert response.get_json()["success"] is False


def test_invalid_duration_rejected(client, registered_user, test_assessment):
    """13. Validate zero or negative duration returns 422."""
    sym_res = client.get("/api/v1/symptoms")
    symptom_id = sym_res.get_json()["data"][0]["id"]

    # Negative duration
    res1 = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={
            "symptom_id": symptom_id,
            "severity": "mild",
            "duration_value": -5,
            "duration_unit": "days",
        },
    )
    assert res1.status_code == 422

    # Invalid unit
    res2 = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={
            "symptom_id": symptom_id,
            "severity": "mild",
            "duration_value": 2,
            "duration_unit": "centuries",
        },
    )
    assert res2.status_code == 422


def test_invalid_observation_value_rejected(client, registered_user, test_assessment):
    """14. Validate unrecognized observation choice returns 422."""
    response = client.put(
        f"/api/v1/assessments/{test_assessment['id']}/observations",
        headers=registered_user["headers"],
        json={"appetite": "ravenous_monster"},  # Invalid
    )
    assert response.status_code == 422
    assert response.get_json()["success"] is False


# -----------------------------------------------------------------------------
# 5. Multi-Tenant Security & Ownership Isolation
# -----------------------------------------------------------------------------

def test_cannot_create_assessment_for_another_users_pet(client, registered_user, second_user_pet):
    """18. CRITICAL SECURITY: User cannot create an assessment for someone else's pet."""
    response = client.post(
        f"/api/v1/pets/{second_user_pet['id']}/assessments",
        headers=registered_user["headers"],
    )
    assert response.status_code == 403
    assert response.get_json()["success"] is False


def test_unauthorized_assessment_access(client, second_user, test_assessment):
    """15. CRITICAL SECURITY: User cannot view another user's assessment."""
    response = client.get(
        f"/api/v1/assessments/{test_assessment['id']}",
        headers=second_user["headers"],
    )
    assert response.status_code == 403
    assert response.get_json()["success"] is False


def test_unauthorized_assessment_modification(client, second_user, test_assessment):
    """16. CRITICAL SECURITY: User cannot modify another user's assessment."""
    # Attempt status update
    res1 = client.put(
        f"/api/v1/assessments/{test_assessment['id']}",
        headers=second_user["headers"],
        json={"status": "completed"},
    )
    assert res1.status_code == 403

    # Attempt adding observations
    res2 = client.put(
        f"/api/v1/assessments/{test_assessment['id']}/observations",
        headers=second_user["headers"],
        json={"appetite": "decreased"},
    )
    assert res2.status_code == 403


def test_unauthorized_assessment_deletion(client, second_user, test_assessment):
    """17. CRITICAL SECURITY: User cannot delete another user's assessment."""
    response = client.delete(
        f"/api/v1/assessments/{test_assessment['id']}",
        headers=second_user["headers"],
    )
    assert response.status_code == 403
    assert response.get_json()["success"] is False


# -----------------------------------------------------------------------------
# 6. AI-Ready Data Transformation & Emergency Triage Evaluation
# -----------------------------------------------------------------------------

def test_ai_data_transformation(client, registered_user, test_assessment):
    """20. Validate conversion into structured AI-ready data format."""
    # Add symptom
    sym_res = client.get("/api/v1/symptoms?category=Respiratory")
    symptom_id = sym_res.get_json()["data"][0]["id"]
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={
            "symptom_id": symptom_id,
            "severity": "severe",
            "duration_value": 3,
            "duration_unit": "days",
            "notes": "Wheezing at night",
        },
    )

    # Add observations
    client.put(
        f"/api/v1/assessments/{test_assessment['id']}/observations",
        headers=registered_user["headers"],
        json={
            "appetite": "decreased",
            "breathing_change": "labored",
            "pain_observed": "severe",
        },
    )

    # Add note
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/notes",
        headers=registered_user["headers"],
        json={"note": "Pet is reluctant to lie down."},
    )

    # Retrieve AI-ready payload via endpoint
    res = client.get(
        f"/api/v1/assessments/{test_assessment['id']}/ai-data",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    data = res.get_json()["data"]

    ai_input = data["ai_input"]
    assert "pet" in ai_input
    assert ai_input["pet"]["species"] == "Canine"
    assert "symptoms" in ai_input
    assert len(ai_input["symptoms"]) == 1
    assert ai_input["symptoms"][0]["duration"]["value"] == 3.0
    assert ai_input["symptoms"][0]["duration"]["unit"] == "days"
    assert ai_input["observations"]["breathing_change"] == "labored"
    assert "reluctant to lie down" in ai_input["additional_notes"]

    # Verify Emergency screening classification
    emergency = data["emergency_screening"]
    assert emergency["is_emergency_flagged"] is True
    assert emergency["risk_level"] == "emergency"
    assert len(emergency["flags"]) >= 1
    assert "disclaimer" in emergency

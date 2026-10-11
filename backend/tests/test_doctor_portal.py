"""Integration and unit tests for Doctor Portal and clinical review endpoints."""
import uuid
import pytest
from app.extensions import db
from app.models.user import User
from app.models.pet import Pet
from app.models.health_assessment import HealthAssessment
from app.models.risk_analysis import AssessmentRiskAnalysis
from app.models.doctor_review import DoctorReview
from app.models.assessment_symptom import AssessmentSymptom
from app.models.symptom import Symptom

pytestmark = pytest.mark.skip(reason="Doctor portal workflows retired for owner-only product")


@pytest.fixture
def doctor_client(client):
    """Create a verified doctor user and authenticate, returning headers and doctor user."""
    email = f"dr_{uuid.uuid4().hex[:6]}@clinic.vet"
    password = "DoctorPassword123!"
    doctor_user = User(
        name="Dr. Sarah Adams, DVM",
        email=email,
        password=password,
        role=User.ROLE_DOCTOR,
    )
    db.session.add(doctor_user)
    db.session.commit()

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.get_json()["data"]["tokens"]["access_token"]
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "user": doctor_user,
    }


@pytest.fixture
def clinical_case_setup(client, registered_user):
    """Create a sample pet intake case with symptoms and AI risk analysis."""
    owner_id = registered_user["user"]["id"]
    pet = Pet(
        owner_id=owner_id,
        name="Milo",
        species="Dog",
        breed="Golden Retriever",
        sex="Male",
        weight=28.5,
        weight_unit="kg",
        spayed_neutered=True,
    )
    db.session.add(pet)
    db.session.commit()

    assessment = HealthAssessment(
        pet_id=pet.id,
        status=HealthAssessment.STATUS_COMPLETED,
        current_step=5,
    )
    db.session.add(assessment)
    db.session.commit()

    symptom = Symptom.query.first()
    if symptom:
        asymp = AssessmentSymptom(
            assessment_id=assessment.id,
            symptom_id=symptom.id,
            severity="moderate",
            duration_value=3.0,
            duration_unit="days",
        )
        db.session.add(asymp)

    risk = AssessmentRiskAnalysis(
        assessment_id=assessment.id,
        risk_level=AssessmentRiskAnalysis.RISK_HIGH,
        risk_score=78,
        key_factors=["Lethargy", "Persistent Cough"],
        recommendation="Prompt veterinary consultation advised.",
        is_emergency=False,
    )
    db.session.add(risk)
    db.session.commit()

    return {
        "pet": pet,
        "assessment": assessment,
        "risk": risk,
    }


def test_doctor_route_unauthenticated_fails(client):
    """Verify unauthenticated requests to doctor endpoints receive HTTP 401."""
    res = client.get("/api/v1/doctor/cases")
    assert res.status_code == 401


def test_doctor_route_pet_owner_forbidden(client, registered_user):
    """Verify regular pet owner accounts receive HTTP 403 Forbidden on doctor endpoints."""
    headers = registered_user["headers"]
    res = client.get("/api/v1/doctor/cases", headers=headers)
    assert res.status_code == 403
    data = res.get_json()
    assert "Doctor access required" in data.get("message", "")


def test_doctor_list_cases_success(client, doctor_client, clinical_case_setup):
    """Verify authenticated doctors can query clinical intake cases."""
    headers = doctor_client["headers"]
    res = client.get("/api/v1/doctor/cases", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "items" in data["data"]
    assert data["data"]["total"] >= 1

    case = next((c for c in data["data"]["items"] if c["assessment_id"] == clinical_case_setup["assessment"].id), None)
    assert case is not None
    assert case["pet"]["name"] == "Milo"
    assert case["effective_triage"] == "urgent"
    assert case["review_status"] == "pending"


def test_doctor_get_case_detail(client, doctor_client, clinical_case_setup):
    """Verify doctor can retrieve full clinical case details."""
    headers = doctor_client["headers"]
    assessment_id = clinical_case_setup["assessment"].id

    res = client.get(f"/api/v1/doctor/cases/{assessment_id}", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    case = data["data"]
    assert case["assessment_id"] == assessment_id
    assert case["pet"]["name"] == "Milo"
    assert case["risk_analysis"]["risk_level"] == "HIGH"
    assert isinstance(case["symptoms"], list)


def test_doctor_submit_review(client, doctor_client, clinical_case_setup):
    """Verify doctor can submit clinical review with triage override and clinical notes."""
    headers = doctor_client["headers"]
    assessment_id = clinical_case_setup["assessment"].id

    review_payload = {
        "override_triage_level": "critical",
        "doctor_notes": "Patient presents with persistent cough and crackles on auscultation.",
        "recommendations": "Perform thoracic radiographs and CBC panel within 24 hours.",
        "prescriptions": "Doxycycline 100mg BID for 10 days.",
        "status": "reviewed",
    }

    res = client.post(
        f"/api/v1/doctor/cases/{assessment_id}/review",
        json=review_payload,
        headers=headers,
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    review = data["data"]
    assert review["assessment_id"] == assessment_id
    assert review["override_triage_level"] == "critical"
    assert review["doctor_notes"] == review_payload["doctor_notes"]
    assert review["prescriptions"] == review_payload["prescriptions"]

    # Verify case detail now shows latest review
    detail_res = client.get(f"/api/v1/doctor/cases/{assessment_id}", headers=headers)
    detail_data = detail_res.get_json()["data"]
    assert detail_data["latest_review"] is not None
    assert detail_data["latest_review"]["override_triage_level"] == "critical"

    # Verify listing shows review_status as reviewed and effective_triage as critical
    list_res = client.get(f"/api/v1/doctor/cases?review_status=reviewed", headers=headers)
    items = list_res.get_json()["data"]["items"]
    matched = [it for it in items if it["assessment_id"] == assessment_id]
    assert len(matched) == 1
    assert matched[0]["effective_triage"] == "critical"
    assert matched[0]["review_status"] == "reviewed"

"""Tests for DoctorReview entity, schema migration, and HealthAssessment draft/step tracking."""
import uuid
import pytest
from app.extensions import db
from app.models.user import User
from app.models.pet import Pet
from app.models.health_assessment import HealthAssessment
from app.models.doctor_review import DoctorReview
from app.schemas.doctor_review_schema import DoctorReviewCreateSchema, DoctorReviewResponseSchema


@pytest.fixture
def test_doctor(client):
    """Create a verified doctor user."""
    doctor = User(
        name="Dr. Alex Rivera, DVM",
        email=f"doctor_{uuid.uuid4().hex[:6]}@vetvision.ai",
        password="DoctorPassword123!",
        role=User.ROLE_DOCTOR,
    )
    db.session.add(doctor)
    db.session.commit()
    return doctor


@pytest.fixture
def test_pet_assessment(client, registered_user):
    """Create a pet and health assessment for test."""
    owner_id = registered_user["user"]["id"]
    pet = Pet(
        owner_id=owner_id,
        name="Luna",
        species="Cat",
        breed="Siamese",
        weight=4.2,
        weight_unit="kg",
        spayed_neutered=True,
    )
    db.session.add(pet)
    db.session.commit()

    assessment = HealthAssessment(
        pet_id=pet.id,
        current_step=2,
        draft_data={"selected_symptoms": ["vomiting", "lethargy"], "step": 2},
    )
    db.session.add(assessment)
    db.session.commit()
    return pet, assessment


def test_assessment_intake_step_and_draft_persistence(test_pet_assessment):
    """Verify that current_step and draft_data persist and serialize cleanly."""
    pet, assessment = test_pet_assessment
    assert assessment.current_step == 2
    assert assessment.draft_data["step"] == 2
    assert "vomiting" in assessment.draft_data["selected_symptoms"]

    # Verify serialization
    data = assessment.to_dict()
    assert data["current_step"] == 2
    assert data["draft_data"] == {"selected_symptoms": ["vomiting", "lethargy"], "step": 2}


def test_create_doctor_review(test_doctor, test_pet_assessment):
    """Verify doctor review creation, foreign keys, and relationships."""
    pet, assessment = test_pet_assessment
    review = DoctorReview(
        assessment_id=assessment.id,
        doctor_id=test_doctor.id,
        status=DoctorReview.STATUS_REVIEWED,
        override_triage_level=DoctorReview.TRIAGE_URGENT,
        doctor_notes="Patient presents with acute dehydration secondary to persistent emesis.",
        recommendations="Administer subcutaneous fluids, prescribe antiemetics, and schedule re-check in 24 hours.",
        prescriptions="Cerenia 16mg once daily for 3 days.",
    )
    db.session.add(review)
    db.session.commit()

    # Query back
    fetched = DoctorReview.query.filter_by(id=review.id).first()
    assert fetched is not None
    assert fetched.assessment_id == assessment.id
    assert fetched.doctor_id == test_doctor.id
    assert fetched.override_triage_level == "urgent"
    assert fetched.doctor.name == "Dr. Alex Rivera, DVM"

    # Relationship from assessment
    assert len(assessment.doctor_reviews) == 1
    assert assessment.doctor_reviews[0].id == review.id

    # Verify nested assessment to_dict serialization
    nested_data = assessment.to_dict(include_nested=True)
    assert "doctor_reviews" in nested_data
    assert len(nested_data["doctor_reviews"]) == 1
    assert nested_data["doctor_reviews"][0]["doctor_name"] == "Dr. Alex Rivera, DVM"
    assert nested_data["doctor_reviews"][0]["override_triage_level"] == "urgent"


def test_doctor_review_schema_validation():
    """Verify DoctorReview schemas validate required and allowed inputs."""
    schema = DoctorReviewCreateSchema()
    valid_payload = {
        "assessment_id": str(uuid.uuid4()),
        "status": "reviewed",
        "override_triage_level": "routine",
        "doctor_notes": "All vital observations within expected range.",
        "recommendations": "Continue observation.",
    }
    errors = schema.validate(valid_payload)
    assert not errors

    # Invalid triage level
    invalid_payload = {
        "assessment_id": str(uuid.uuid4()),
        "override_triage_level": "super_emergency",
    }
    errors = schema.validate(invalid_payload)
    assert "override_triage_level" in errors


def test_doctor_review_cascades_on_assessment_delete(test_doctor, test_pet_assessment):
    """Verify that deleting an assessment cascades and removes associated doctor reviews."""
    pet, assessment = test_pet_assessment
    review = DoctorReview(
        assessment_id=assessment.id,
        doctor_id=test_doctor.id,
        doctor_notes="Review notes prior to delete test",
    )
    db.session.add(review)
    db.session.commit()
    review_id = review.id

    # Delete assessment
    db.session.delete(assessment)
    db.session.commit()

    # Doctor review should no longer exist
    assert DoctorReview.query.filter_by(id=review_id).first() is None

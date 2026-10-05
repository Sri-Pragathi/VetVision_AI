"""Assessment service handling triage intake, symptoms, observations, and notes."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.extensions import db
from app.models.pet import Pet
from app.models.symptom import Symptom
from app.models.health_assessment import HealthAssessment
from app.models.assessment_symptom import AssessmentSymptom
from app.models.health_observation import HealthObservation
from app.models.assessment_note import AssessmentNote
from app.utils.error_handlers import (
    NotFoundException,
    ForbiddenException,
    ValidationException,
    ConflictException,
)


class AssessmentService:
    """Service encapsulating health assessment workflows and ownership isolation."""

    @staticmethod
    def _verify_pet_ownership(pet_id: str, user_id: str) -> Pet:
        """Verify that the pet exists and belongs to the authenticated user."""
        pet = db.session.get(Pet, pet_id)
        if not pet:
            raise NotFoundException("Pet not found.")
        if pet.owner_id != user_id:
            raise ForbiddenException("You do not have permission to access this pet.")
        return pet

    @staticmethod
    def _verify_assessment_ownership(assessment_id: str, user_id: str) -> HealthAssessment:
        """Verify that the health assessment exists and belongs to the authenticated user's pet."""
        assessment = db.session.get(HealthAssessment, assessment_id)
        if not assessment:
            raise NotFoundException("Health assessment not found.")
        
        # Verify ownership through Pet -> User relationship
        if not assessment.pet or assessment.pet.owner_id != user_id:
            raise ForbiddenException("You do not have permission to access this health assessment.")
        return assessment

    @staticmethod
    def create_assessment(pet_id: str, user_id: str) -> Dict[str, Any]:
        """Initiate a new health assessment session for a pet."""
        pet = AssessmentService._verify_pet_ownership(pet_id, user_id)

        assessment = HealthAssessment(
            pet_id=pet.id,
            status=HealthAssessment.STATUS_IN_PROGRESS,
            started_at=datetime.now(timezone.utc),
        )
        db.session.add(assessment)
        db.session.commit()
        return assessment.to_dict()

    @staticmethod
    def get_pet_assessments(pet_id: str, user_id: str) -> List[Dict[str, Any]]:
        """List all assessments for a specific pet owned by the user."""
        AssessmentService._verify_pet_ownership(pet_id, user_id)
        assessments = (
            HealthAssessment.query.filter_by(pet_id=pet_id)
            .order_by(HealthAssessment.started_at.desc())
            .all()
        )
        return [a.to_dict() for a in assessments]

    @staticmethod
    def get_assessment_by_id(assessment_id: str, user_id: str) -> Dict[str, Any]:
        """Fetch details of a specific assessment."""
        assessment = AssessmentService._verify_assessment_ownership(assessment_id, user_id)
        return assessment.to_dict()

    @staticmethod
    def update_assessment_status(
        assessment_id: str, user_id: str, new_status: str
    ) -> Dict[str, Any]:
        """Update assessment lifecycle status with strict transition validation."""
        assessment = AssessmentService._verify_assessment_ownership(assessment_id, user_id)
        current_status = assessment.status

        if current_status == new_status:
            return assessment.to_dict()

        # Lifecycle state transitions
        if current_status == HealthAssessment.STATUS_COMPLETED:
            raise ValidationException(
                "Cannot change status of an already completed assessment."
            )
        
        if current_status == HealthAssessment.STATUS_CANCELLED:
            raise ValidationException(
                "Cannot change status of a cancelled assessment."
            )

        if new_status == HealthAssessment.STATUS_COMPLETED:
            assessment.complete()
        elif new_status == HealthAssessment.STATUS_CANCELLED:
            assessment.cancel()
        elif new_status == HealthAssessment.STATUS_IN_PROGRESS:
            assessment.status = HealthAssessment.STATUS_IN_PROGRESS
        else:
            raise ValidationException(f"Unsupported status transition: {new_status}")

        db.session.commit()
        return assessment.to_dict()

    @staticmethod
    def delete_assessment(assessment_id: str, user_id: str) -> None:
        """Delete an assessment session and its cascading child records."""
        assessment = AssessmentService._verify_assessment_ownership(assessment_id, user_id)
        db.session.delete(assessment)
        db.session.commit()

    # ----------------------------------------------------
    # Symptoms Association Management
    # ----------------------------------------------------

    @staticmethod
    def add_symptom_to_assessment(
        assessment_id: str, user_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Attach a clinical symptom with severity and duration to an assessment."""
        assessment = AssessmentService._verify_assessment_ownership(assessment_id, user_id)
        symptom_id = data["symptom_id"]

        symptom = db.session.get(Symptom, symptom_id)
        if not symptom:
            raise NotFoundException(f"Symptom with ID '{symptom_id}' does not exist.")

        # Check if already added to this assessment
        existing = AssessmentSymptom.query.filter_by(
            assessment_id=assessment.id, symptom_id=symptom_id
        ).first()

        if existing:
            # Update existing entry
            existing.severity = data["severity"]
            existing.duration_value = float(data["duration_value"])
            existing.duration_unit = data["duration_unit"]
            existing.notes = data.get("notes")
            db.session.commit()
            return existing.to_dict()

        entry = AssessmentSymptom(
            assessment_id=assessment.id,
            symptom_id=symptom.id,
            severity=data["severity"],
            duration_value=float(data["duration_value"]),
            duration_unit=data["duration_unit"],
            notes=data.get("notes"),
        )
        db.session.add(entry)
        db.session.commit()
        return entry.to_dict()

    @staticmethod
    def update_assessment_symptom(
        assessment_id: str, symptom_id: str, user_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an attached symptom's severity, duration, or notes."""
        assessment = AssessmentService._verify_assessment_ownership(assessment_id, user_id)

        entry = AssessmentSymptom.query.filter_by(
            assessment_id=assessment.id, symptom_id=symptom_id
        ).first()

        if not entry:
            raise NotFoundException("Symptom is not currently attached to this assessment.")

        if "severity" in data and data["severity"]:
            entry.severity = data["severity"]
        if "duration_value" in data and data["duration_value"] is not None:
            entry.duration_value = float(data["duration_value"])
        if "duration_unit" in data and data["duration_unit"]:
            entry.duration_unit = data["duration_unit"]
        if "notes" in data:
            entry.notes = data["notes"]

        db.session.commit()
        return entry.to_dict()

    @staticmethod
    def remove_assessment_symptom(
        assessment_id: str, symptom_id: str, user_id: str
    ) -> None:
        """Detach a symptom from an assessment."""
        assessment = AssessmentService._verify_assessment_ownership(assessment_id, user_id)

        entry = AssessmentSymptom.query.filter_by(
            assessment_id=assessment.id, symptom_id=symptom_id
        ).first()

        if not entry:
            raise NotFoundException("Symptom is not attached to this assessment.")

        db.session.delete(entry)
        db.session.commit()

    # ----------------------------------------------------
    # Structured Health Observations Management
    # ----------------------------------------------------

    @staticmethod
    def upsert_observations(
        assessment_id: str, user_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create or update structured clinical observations for an assessment."""
        assessment = AssessmentService._verify_assessment_ownership(assessment_id, user_id)

        obs = HealthObservation.query.filter_by(assessment_id=assessment.id).first()
        if not obs:
            obs = HealthObservation(assessment_id=assessment.id)
            db.session.add(obs)

        # Update valid fields
        updatable = [
            "appetite",
            "water_intake",
            "activity_level",
            "behaviour_change",
            "sleep_change",
            "stool_change",
            "urine_change",
            "breathing_change",
            "pain_observed",
        ]
        for field in updatable:
            if field in data:
                setattr(obs, field, data[field])

        db.session.commit()
        return obs.to_dict()

    # ----------------------------------------------------
    # Assessment Notes Management
    # ----------------------------------------------------

    @staticmethod
    def add_note(assessment_id: str, user_id: str, note_text: str) -> Dict[str, Any]:
        """Add a free-text clinical or owner note to an assessment."""
        assessment = AssessmentService._verify_assessment_ownership(assessment_id, user_id)

        note = AssessmentNote(
            assessment_id=assessment.id,
            note=note_text.strip(),
        )
        db.session.add(note)
        db.session.commit()
        return note.to_dict()

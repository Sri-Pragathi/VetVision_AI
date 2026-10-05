"""HealthObservation model for structured physiological and behavioral metrics."""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from app.extensions import db


class HealthObservation(db.Model):
    """Structured observations relevant to clinical triage and AI risk scoring."""
    __tablename__ = "health_observations"

    # Controlled observation vocabularies
    APPETITE_CHOICES = {"normal", "decreased", "increased", "none"}
    WATER_INTAKE_CHOICES = {"normal", "decreased", "increased", "excessive"}
    ACTIVITY_LEVEL_CHOICES = {"normal", "lethargic", "depressed", "hyperactive"}
    BEHAVIOUR_CHANGE_CHOICES = {"none", "mild", "aggressive", "withdrawn", "restless"}
    SLEEP_CHANGE_CHOICES = {"normal", "sleeping_more", "sleeping_less", "restless_sleep"}
    STOOL_CHANGE_CHOICES = {"normal", "soft", "watery_diarrhea", "constipated", "blood_present"}
    URINE_CHANGE_CHOICES = {"normal", "frequent", "straining", "discolored", "blood_present"}
    BREATHING_CHANGE_CHOICES = {"normal", "rapid", "shallow", "labored", "wheezing"}
    PAIN_OBSERVED_CHOICES = {"none", "mild_vocalizing", "guarding_area", "reluctant_to_move", "severe"}

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    assessment_id = db.Column(
        db.String(36),
        db.ForeignKey("health_assessments.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    appetite = db.Column(db.String(50), nullable=True)
    water_intake = db.Column(db.String(50), nullable=True)
    activity_level = db.Column(db.String(50), nullable=True)
    behaviour_change = db.Column(db.String(50), nullable=True)
    sleep_change = db.Column(db.String(50), nullable=True)
    stool_change = db.Column(db.String(50), nullable=True)
    urine_change = db.Column(db.String(50), nullable=True)
    breathing_change = db.Column(db.String(50), nullable=True)
    pain_observed = db.Column(db.String(50), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    assessment = db.relationship("HealthAssessment", back_populates="observations")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize health observations."""
        return {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "appetite": self.appetite,
            "water_intake": self.water_intake,
            "activity_level": self.activity_level,
            "behaviour_change": self.behaviour_change,
            "sleep_change": self.sleep_change,
            "stool_change": self.stool_change,
            "urine_change": self.urine_change,
            "breathing_change": self.breathing_change,
            "pain_observed": self.pain_observed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<HealthObservation for assessment {self.assessment_id}>"

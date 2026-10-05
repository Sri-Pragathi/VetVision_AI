"""AssessmentSymptom model linking health assessments with clinical symptoms."""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from app.extensions import db


class AssessmentSymptom(db.Model):
    """Association model linking a HealthAssessment to a Symptom with clinical details."""
    __tablename__ = "assessment_symptoms"

    # Validation constants
    SEVERITY_MILD = "mild"
    SEVERITY_MODERATE = "moderate"
    SEVERITY_SEVERE = "severe"
    VALID_SEVERITIES = {SEVERITY_MILD, SEVERITY_MODERATE, SEVERITY_SEVERE}

    UNIT_HOURS = "hours"
    UNIT_DAYS = "days"
    UNIT_WEEKS = "weeks"
    UNIT_MONTHS = "months"
    VALID_DURATION_UNITS = {UNIT_HOURS, UNIT_DAYS, UNIT_WEEKS, UNIT_MONTHS}

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    assessment_id = db.Column(
        db.String(36),
        db.ForeignKey("health_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    symptom_id = db.Column(
        db.String(36),
        db.ForeignKey("symptoms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    severity = db.Column(db.String(20), nullable=False)
    duration_value = db.Column(db.Float, nullable=False)
    duration_unit = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, nullable=True)

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
    assessment = db.relationship("HealthAssessment", back_populates="symptoms")
    symptom = db.relationship("Symptom", back_populates="assessment_associations")

    __table_args__ = (
        db.UniqueConstraint("assessment_id", "symptom_id", name="uq_assessment_symptom"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize assessment symptom entity."""
        symptom_name = self.symptom.name if self.symptom else None
        symptom_category = self.symptom.category if self.symptom else None

        return {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "symptom_id": self.symptom_id,
            "symptom_name": symptom_name,
            "symptom_category": symptom_category,
            "severity": self.severity,
            "duration_value": self.duration_value,
            "duration_unit": self.duration_unit,
            "duration": {
                "value": self.duration_value,
                "unit": self.duration_unit,
            },
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<AssessmentSymptom {self.symptom_id} in {self.assessment_id} ({self.severity})>"

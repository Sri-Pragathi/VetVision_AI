"""DoctorReview model representing clinical review, triage override, and doctor notes."""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.extensions import db


class DoctorReview(db.Model):
    """Clinical assessment review written by an authorized veterinarian/doctor."""
    __tablename__ = "doctor_reviews"

    STATUS_PENDING = "pending"
    STATUS_REVIEWED = "reviewed"
    VALID_STATUSES = {STATUS_PENDING, STATUS_REVIEWED}

    TRIAGE_NON_URGENT = "non_urgent"
    TRIAGE_ROUTINE = "routine"
    TRIAGE_URGENT = "urgent"
    TRIAGE_CRITICAL = "critical"
    VALID_TRIAGE_LEVELS = {TRIAGE_NON_URGENT, TRIAGE_ROUTINE, TRIAGE_URGENT, TRIAGE_CRITICAL}

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
    doctor_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = db.Column(
        db.String(20),
        nullable=False,
        default=STATUS_REVIEWED,
        server_default=STATUS_REVIEWED,
    )
    override_triage_level = db.Column(
        db.String(20),
        nullable=True,
    )
    doctor_notes = db.Column(
        db.Text,
        nullable=True,
    )
    recommendations = db.Column(
        db.Text,
        nullable=True,
    )
    prescriptions = db.Column(
        db.Text,
        nullable=True,
    )
    reviewed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
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
    assessment = db.relationship("HealthAssessment", back_populates="doctor_reviews")
    doctor = db.relationship("User", backref=db.backref("doctor_reviews", lazy="select", cascade="all, delete-orphan"))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize doctor review entity to dictionary."""
        return {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "doctor_id": self.doctor_id,
            "doctor_name": self.doctor.name if self.doctor else None,
            "status": self.status,
            "override_triage_level": self.override_triage_level,
            "doctor_notes": self.doctor_notes,
            "recommendations": self.recommendations,
            "prescriptions": self.prescriptions,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<DoctorReview {self.id} (Assessment: {self.assessment_id}, Doctor: {self.doctor_id})>"

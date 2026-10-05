"""HealthAssessment model representing a clinical checkup or triage intake session."""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.extensions import db


class HealthAssessment(db.Model):
    """Health assessment entity tracking a pet's health intake session."""
    __tablename__ = "health_assessments"

    # Status Constants
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    VALID_STATUSES = {STATUS_IN_PROGRESS, STATUS_COMPLETED, STATUS_CANCELLED}

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    pet_id = db.Column(
        db.String(36),
        db.ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = db.Column(
        db.String(20),
        nullable=False,
        default=STATUS_IN_PROGRESS,
    )
    started_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
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
    pet = db.relationship("Pet", back_populates="health_assessments")

    symptoms = db.relationship(
        "AssessmentSymptom",
        back_populates="assessment",
        cascade="all, delete-orphan",
        lazy="select",
    )

    observations = db.relationship(
        "HealthObservation",
        back_populates="assessment",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="select",
    )

    notes = db.relationship(
        "AssessmentNote",
        back_populates="assessment",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="AssessmentNote.created_at.asc()",
    )

    def complete(self) -> None:
        """Mark assessment as completed and set completion timestamp."""
        self.status = self.STATUS_COMPLETED
        self.completed_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        """Mark assessment as cancelled."""
        self.status = self.STATUS_CANCELLED

    def to_dict(self, include_nested: bool = True) -> Dict[str, Any]:
        """Serialize assessment entity."""
        res: Dict[str, Any] = {
            "id": self.id,
            "pet_id": self.pet_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_nested:
            res["symptoms"] = [s.to_dict() for s in self.symptoms] if self.symptoms else []
            res["observations"] = self.observations.to_dict() if self.observations else None
            res["notes"] = [n.to_dict() for n in self.notes] if self.notes else []

        return res

    def __repr__(self) -> str:
        return f"<HealthAssessment {self.id} (Pet: {self.pet_id}, Status: {self.status})>"

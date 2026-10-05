"""AssessmentNote model representing free-text clinical or owner notes."""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from app.extensions import db


class AssessmentNote(db.Model):
    """Free-text note attached to a HealthAssessment session."""
    __tablename__ = "assessment_notes"

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
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    assessment = db.relationship("HealthAssessment", back_populates="notes")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize assessment note."""
        return {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<AssessmentNote {self.id} for assessment {self.assessment_id}>"

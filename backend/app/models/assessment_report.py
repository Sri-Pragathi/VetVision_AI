"""AssessmentReport model storing versioned, immutable snapshots of clinical assessments."""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.extensions import db


class AssessmentReport(db.Model):
    """Stores versioned, immutable veterinary reports and health summaries.

    Each report is a permanent point-in-time snapshot of the assessment state,
    pet profile, symptoms, observations, image analysis, and AI risk analysis.
    Subsequent assessment edits or re-runs generate a new version rather than
    overwriting historical snapshots.
    """

    __tablename__ = "assessment_reports"

    # Status constants
    STATUS_GENERATED = "GENERATED"
    STATUS_UPDATED = "UPDATED"
    STATUS_ARCHIVED = "ARCHIVED"

    VALID_STATUSES = {
        STATUS_GENERATED,
        STATUS_UPDATED,
        STATUS_ARCHIVED,
    }

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
    report_version = db.Column(db.Integer, nullable=False, default=1)
    report_status = db.Column(
        db.String(30),
        nullable=False,
        default=STATUS_GENERATED,
    )
    generated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    generated_by = db.Column(db.String(36), nullable=False)
    report_data = db.Column(db.JSON, nullable=False)
    disclaimer = db.Column(
        db.Text,
        nullable=False,
        default=(
            "VetVision AI provides AI-assisted health risk and early-warning information "
            "for informational and triage support. It does not provide a definitive "
            "veterinary diagnosis and does not replace examination or advice from a "
            "qualified veterinarian. Seek professional veterinary care when symptoms "
            "are concerning, worsening, or urgent."
        ),
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
    assessment = db.relationship("HealthAssessment", back_populates="reports")

    # Table constraints: Unique report version per assessment
    __table_args__ = (
        db.UniqueConstraint(
            "assessment_id",
            "report_version",
            name="uq_assessment_report_version",
        ),
    )

    def to_dict(self, include_full_data: bool = True) -> Dict[str, Any]:
        """Serialize report entity to dictionary."""
        data: Dict[str, Any] = {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "report_version": self.report_version,
            "report_status": self.report_status,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "generated_by": self.generated_by,
            "disclaimer": self.disclaimer,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_full_data:
            data["report_data"] = self.report_data
        else:
            # Summary overview for list views
            summary_info = (self.report_data or {}).get("risk_analysis", {})
            data["summary"] = {
                "risk_level": summary_info.get("risk_level"),
                "risk_score": summary_info.get("risk_score"),
                "is_emergency": summary_info.get("is_emergency"),
            }
        return data

    def __repr__(self) -> str:
        return (
            f"<AssessmentReport {self.id} "
            f"(Assessment: {self.assessment_id}, v{self.report_version}, status={self.report_status})>"
        )

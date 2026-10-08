"""AssessmentRiskAnalysis model for storing explainable health risk evaluations."""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.extensions import db


class AssessmentRiskAnalysis(db.Model):
    """Stores the explainable AI health risk analysis for a health assessment.

    Each assessment can have one active risk analysis record.
    Re-running analysis updates this record cleanly.
    """

    __tablename__ = "assessment_risk_analyses"

    # Risk level constants
    RISK_LOW = "LOW"
    RISK_MODERATE = "MODERATE"
    RISK_HIGH = "HIGH"
    RISK_EMERGENCY = "EMERGENCY"

    VALID_RISK_LEVELS = {
        RISK_LOW,
        RISK_MODERATE,
        RISK_HIGH,
        RISK_EMERGENCY,
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
        unique=True,
        index=True,
    )
    risk_level = db.Column(db.String(20), nullable=False)
    risk_score = db.Column(db.Integer, nullable=False)
    key_factors = db.Column(db.JSON, nullable=False, default=list)
    factor_breakdown = db.Column(db.JSON, nullable=False, default=dict)
    recommendation = db.Column(db.Text, nullable=False)
    is_emergency = db.Column(db.Boolean, nullable=False, default=False)
    engine_version = db.Column(db.String(50), nullable=False, default="v1.0.0-rule_hybrid")
    disclaimer = db.Column(
        db.Text,
        nullable=False,
        default=(
            "This assessment is for early-warning support and does not replace "
            "professional veterinary diagnosis. If your pet is in acute distress, "
            "contact an emergency veterinary hospital immediately."
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
    assessment = db.relationship("HealthAssessment", back_populates="risk_analysis")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize risk analysis record to dictionary."""
        return {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "key_factors": self.key_factors or [],
            "factor_breakdown": self.factor_breakdown or {},
            "recommendation": self.recommendation,
            "emergency": self.is_emergency,
            "is_emergency": self.is_emergency,
            "engine_version": self.engine_version,
            "disclaimer": self.disclaimer,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<AssessmentRiskAnalysis {self.id} "
            f"(Assessment: {self.assessment_id}, Level: {self.risk_level}, Score: {self.risk_score})>"
        )

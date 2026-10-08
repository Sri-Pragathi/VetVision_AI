"""AssessmentImage and ImageObservation models for pet image attachments and visual analysis."""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.extensions import db


class AssessmentImage(db.Model):
    """Stores pet photographic attachments tied to a clinical health assessment."""

    __tablename__ = "assessment_images"

    # Processing status constants
    STATUS_UPLOADED = "UPLOADED"
    STATUS_VALIDATING = "VALIDATING"
    STATUS_READY = "READY"
    STATUS_ANALYZING = "ANALYZING"
    STATUS_ANALYZED = "ANALYZED"
    STATUS_FAILED = "FAILED"

    VALID_PROCESSING_STATUSES = {
        STATUS_UPLOADED,
        STATUS_VALIDATING,
        STATUS_READY,
        STATUS_ANALYZING,
        STATUS_ANALYZED,
        STATUS_FAILED,
    }

    # Analysis status constants
    ANALYSIS_PENDING = "PENDING"
    ANALYSIS_ANALYZED = "ANALYZED"
    ANALYSIS_REQUIRES_BETTER_IMAGE = "REQUIRES_BETTER_IMAGE"
    ANALYSIS_FAILED = "FAILED"

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
    pet_id = db.Column(
        db.String(36),
        db.ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    original_filename = db.Column(db.String(255), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # In bytes
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)

    processing_status = db.Column(
        db.String(30),
        nullable=False,
        default=STATUS_UPLOADED,
    )
    analysis_status = db.Column(
        db.String(30),
        nullable=False,
        default=ANALYSIS_PENDING,
    )
    quality_gate = db.Column(db.String(30), nullable=True)

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
    assessment = db.relationship("HealthAssessment", back_populates="images")
    pet = db.relationship("Pet", backref=db.backref("assessment_images", lazy="dynamic"))
    observations = db.relationship(
        "ImageObservation",
        back_populates="assessment_image",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="ImageObservation.created_at.asc()",
    )

    def to_dict(self, include_observations: bool = False) -> Dict[str, Any]:
        """Serialize image entity to dictionary."""
        data: Dict[str, Any] = {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "pet_id": self.pet_id,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "width": self.width,
            "height": self.height,
            "processing_status": self.processing_status,
            "analysis_status": self.analysis_status,
            "quality_gate": self.quality_gate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_observations:
            data["observations"] = [obs.to_dict() for obs in self.observations]
        return data

    def __repr__(self) -> str:
        return f"<AssessmentImage {self.id} ({self.original_filename}, status={self.analysis_status})>"


class ImageObservation(db.Model):
    """Structured computer-vision observations extracted from a pet image."""

    __tablename__ = "image_observations"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    assessment_image_id = db.Column(
        db.String(36),
        db.ForeignKey("assessment_images.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    observation_type = db.Column(db.String(50), nullable=False)  # visual_quality, visual_feature, color_profile
    observation_label = db.Column(db.String(100), nullable=False)  # SUITABLE_FOR_ANALYSIS, LOW_VISIBILITY, etc.
    severity = db.Column(db.String(20), nullable=True)  # normal, mild, moderate, severe
    region = db.Column(db.String(100), nullable=True)  # overall_image, focal_region, coat, skin
    description = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(50), nullable=False, default="computer_vision")
    model_version = db.Column(db.String(50), nullable=False, default="v1.0.0-cv_baseline")
    extra_data = db.Column(db.JSON, nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    assessment_image = db.relationship("AssessmentImage", back_populates="observations")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize visual observation entity."""
        return {
            "id": self.id,
            "assessment_image_id": self.assessment_image_id,
            "observation_type": self.observation_type,
            "observation_label": self.observation_label,
            "severity": self.severity,
            "region": self.region,
            "description": self.description,
            "source": self.source,
            "model_version": self.model_version,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<ImageObservation {self.id} ({self.observation_label}, {self.observation_type})>"

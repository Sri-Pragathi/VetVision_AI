"""FollowUpQuestion and FollowUpQuestionOption models for dynamic assessment questions."""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.extensions import db


class FollowUpQuestion(db.Model):
    """Dynamic follow-up question presented during a health assessment.

    Questions can be associated with specific symptoms, categories, species,
    and age ranges. Emergency-related questions are surfaced before routine ones.
    """

    __tablename__ = "follow_up_questions"

    # --- Controlled Enum Constants ---

    # question_type values
    TYPE_YES_NO = "yes_no"
    TYPE_SINGLE_CHOICE = "single_choice"
    TYPE_MULTIPLE_CHOICE = "multiple_choice"
    TYPE_NUMBER = "number"
    TYPE_TEXT = "text"

    VALID_QUESTION_TYPES = {
        TYPE_YES_NO,
        TYPE_SINGLE_CHOICE,
        TYPE_MULTIPLE_CHOICE,
        TYPE_NUMBER,
        TYPE_TEXT,
    }

    # priority values
    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_EMERGENCY = "emergency"

    VALID_PRIORITIES = {
        PRIORITY_LOW,
        PRIORITY_MEDIUM,
        PRIORITY_HIGH,
        PRIORITY_EMERGENCY,
    }

    # Priority ordering for sorting (lower number = higher priority)
    PRIORITY_ORDER = {
        PRIORITY_EMERGENCY: 0,
        PRIORITY_HIGH: 1,
        PRIORITY_MEDIUM: 2,
        PRIORITY_LOW: 3,
    }

    # --- Columns ---
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(30), nullable=False, default=TYPE_YES_NO)
    category = db.Column(db.String(50), nullable=True, index=True)

    # Priority level – drives ordering so emergency questions surface first
    priority = db.Column(db.String(20), nullable=False, default=PRIORITY_MEDIUM)

    # Optional link to a specific symptom
    symptom_id = db.Column(
        db.String(36),
        db.ForeignKey("symptoms.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Optional species restriction (e.g., "Canine", "Feline") – NULL means all species
    species = db.Column(db.String(50), nullable=True)

    # Optional age range in months – NULL means no restriction
    min_age_months = db.Column(db.Integer, nullable=True)
    max_age_months = db.Column(db.Integer, nullable=True)

    is_emergency_related = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    display_order = db.Column(db.Integer, nullable=False, default=0)

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

    # --- Relationships ---
    symptom = db.relationship("Symptom", backref=db.backref("follow_up_questions", lazy="dynamic"))

    options = db.relationship(
        "FollowUpQuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="FollowUpQuestionOption.display_order.asc()",
        lazy="select",
    )

    answers = db.relationship(
        "AssessmentAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def to_dict(self, include_options: bool = True) -> Dict[str, Any]:
        """Serialize follow-up question entity."""
        result: Dict[str, Any] = {
            "id": self.id,
            "question_text": self.question_text,
            "question_type": self.question_type,
            "category": self.category,
            "priority": self.priority,
            "symptom_id": self.symptom_id,
            "species": self.species,
            "min_age_months": self.min_age_months,
            "max_age_months": self.max_age_months,
            "is_emergency_related": self.is_emergency_related,
            "is_active": self.is_active,
            "display_order": self.display_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_options:
            result["options"] = [opt.to_dict() for opt in self.options]
        return result

    def __repr__(self) -> str:
        return f"<FollowUpQuestion '{self.question_text[:40]}' [{self.priority}]>"


class FollowUpQuestionOption(db.Model):
    """Structured answer option for a FollowUpQuestion.

    Tracks severity weighting and whether selecting this option should
    trigger an emergency flag on the assessment.
    """

    __tablename__ = "follow_up_question_options"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    question_id = db.Column(
        db.String(36),
        db.ForeignKey("follow_up_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_text = db.Column(db.String(255), nullable=False)
    option_value = db.Column(db.String(100), nullable=False)

    # 0.0 – 1.0 scale; higher values are more clinically significant
    severity_weight = db.Column(db.Float, nullable=True)

    # Selecting this option raises an emergency concern flag
    emergency_flag = db.Column(db.Boolean, nullable=False, default=False)

    display_order = db.Column(db.Integer, nullable=False, default=0)

    # --- Relationships ---
    question = db.relationship("FollowUpQuestion", back_populates="options")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize question option entity."""
        return {
            "id": self.id,
            "question_id": self.question_id,
            "option_text": self.option_text,
            "option_value": self.option_value,
            "severity_weight": self.severity_weight,
            "emergency_flag": self.emergency_flag,
            "display_order": self.display_order,
        }

    def __repr__(self) -> str:
        return f"<FollowUpQuestionOption '{self.option_text}' (emergency={self.emergency_flag})>"

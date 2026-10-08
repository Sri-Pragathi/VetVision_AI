"""AssessmentAnswer model recording a user's response to a follow-up question."""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.extensions import db


class AssessmentAnswer(db.Model):
    """Records a single answer submitted during a health assessment.

    An answer is tied to both an assessment and a specific question that was
    generated for that assessment. This prevents arbitrary question injection –
    the service layer enforces that only generated questions can be answered.

    One of the value fields (selected_option_id, answer_text, numeric_value,
    boolean_value) will be populated depending on the question_type.
    """

    __tablename__ = "assessment_answers"

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
    question_id = db.Column(
        db.String(36),
        db.ForeignKey("follow_up_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # For single_choice / yes_no question types
    selected_option_id = db.Column(
        db.String(36),
        db.ForeignKey("follow_up_question_options.id", ondelete="SET NULL"),
        nullable=True,
    )
    # For free-text question types
    answer_text = db.Column(db.Text, nullable=True)
    # For numeric question types
    numeric_value = db.Column(db.Float, nullable=True)
    # For yes_no without an explicit option record
    boolean_value = db.Column(db.Boolean, nullable=True)

    # Cached flag – updated when the answer triggers an emergency indicator
    triggered_emergency = db.Column(db.Boolean, nullable=False, default=False)

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
    assessment = db.relationship(
        "HealthAssessment",
        backref=db.backref("answers", cascade="all, delete-orphan", lazy="dynamic"),
    )
    question = db.relationship("FollowUpQuestion", back_populates="answers")
    selected_option = db.relationship("FollowUpQuestionOption", foreign_keys=[selected_option_id])

    # Unique constraint: one answer per question per assessment
    __table_args__ = (
        db.UniqueConstraint(
            "assessment_id",
            "question_id",
            name="uq_assessment_answer",
        ),
    )

    def to_dict(self, include_question: bool = False) -> Dict[str, Any]:
        """Serialize assessment answer entity."""
        result: Dict[str, Any] = {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "question_id": self.question_id,
            "selected_option_id": self.selected_option_id,
            "answer_text": self.answer_text,
            "numeric_value": self.numeric_value,
            "boolean_value": self.boolean_value,
            "triggered_emergency": self.triggered_emergency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if self.selected_option:
            result["selected_option"] = self.selected_option.to_dict()
        if include_question and self.question:
            result["question"] = self.question.to_dict()
        return result

    def __repr__(self) -> str:
        return (
            f"<AssessmentAnswer question={self.question_id} "
            f"assessment={self.assessment_id}>"
        )

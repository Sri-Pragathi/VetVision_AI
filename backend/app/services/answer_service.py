"""Answer submission service for dynamic follow-up question responses.

Handles validation, ownership enforcement, duplicate detection, and
emergency flag propagation when users submit answers during assessments.
"""
from typing import Dict, Any, List, Optional
from app.extensions import db
from app.models.health_assessment import HealthAssessment
from app.models.follow_up_question import FollowUpQuestion, FollowUpQuestionOption
from app.models.assessment_answer import AssessmentAnswer
from app.services.dynamic_question_service import DynamicQuestionService
from app.services.assessment_service import AssessmentService
from app.utils.error_handlers import (
    NotFoundException,
    ForbiddenException,
    ValidationException,
    ConflictException,
)


class AnswerService:
    """Service for submitting and retrieving assessment answers.

    Enforces security rules:
    - Assessment must belong to the authenticated user's pet.
    - Question must be relevant to the current assessment.
    - Duplicate answers are rejected (one answer per question per assessment).
    - Option must belong to the question being answered.
    - Inactive questions cannot be answered.
    - Completed/cancelled assessments cannot receive new answers.
    """

    @staticmethod
    def _verify_assessment_and_ownership(
        assessment_id: str, user_id: str
    ) -> HealthAssessment:
        """Verify assessment exists and is owned by user."""
        return AssessmentService._verify_assessment_ownership(assessment_id, user_id)

    @staticmethod
    def _verify_question_applicable(
        assessment: HealthAssessment, question_id: str
    ) -> FollowUpQuestion:
        """Verify that a question exists, is active, and is applicable to this assessment.

        Security: prevents users from submitting answers to arbitrary question IDs
        that were not generated for their specific assessment context.
        """
        question = db.session.get(FollowUpQuestion, question_id)
        if not question:
            raise NotFoundException(f"Follow-up question '{question_id}' not found.")

        if not question.is_active:
            raise ValidationException(
                "This question is no longer active and cannot be answered."
            )

        # Verify question is applicable to this assessment's context
        # A question is applicable if:
        # (a) it targets a symptom in this assessment, OR
        # (b) it belongs to a category represented in this assessment's symptoms, OR
        # (c) it has no symptom/category binding (universal question)
        pet = assessment.pet
        pet_species = (pet.species or "").strip() if pet else ""

        # Species check
        if question.species and pet_species:
            if question.species.lower() not in (pet_species.lower(), pet_species.title().lower()):
                raise ValidationException(
                    "This question is not applicable to this pet's species."
                )

        # Collect assessment symptom IDs and categories
        symptom_ids = {a.symptom_id for a in (assessment.symptoms or [])}
        from app.services.dynamic_question_service import SYMPTOM_TO_CATEGORY
        categories = set()
        for assoc in (assessment.symptoms or []):
            name = (assoc.symptom.name.lower() if assoc.symptom else "")
            cat = SYMPTOM_TO_CATEGORY.get(name)
            if cat:
                categories.add(cat)
            elif assoc.symptom:
                categories.add(assoc.symptom.category)

        # Universal questions (no symptom or category binding) are always applicable
        is_universal = (not question.symptom_id) and (not question.category)
        # Symptom-specific match
        is_symptom_match = question.symptom_id and question.symptom_id in symptom_ids
        # Category match
        is_category_match = question.category and question.category in categories

        if not (is_universal or is_symptom_match or is_category_match):
            # Also allow conditional questions triggered by existing answers
            from app.services.dynamic_question_service import CONDITIONAL_TRIGGERS
            conditional_cats = DynamicQuestionService._get_conditional_categories(assessment)
            if question.category not in conditional_cats:
                raise ValidationException(
                    "This question was not generated for the current assessment context."
                )

        return question

    @staticmethod
    def submit_answer(
        assessment_id: str,
        user_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Submit an answer to a follow-up question for a given assessment.

        Args:
            assessment_id: UUID of the assessment.
            user_id: Authenticated user's ID.
            data: Validated answer data dict containing:
                - question_id (required)
                - selected_option_id (optional)
                - answer_text (optional)
                - numeric_value (optional)
                - boolean_value (optional)

        Returns:
            Serialized AssessmentAnswer dict.
        """
        assessment = AnswerService._verify_assessment_and_ownership(assessment_id, user_id)

        # Prevent answering on terminal assessments
        if assessment.status in (
            HealthAssessment.STATUS_COMPLETED,
            HealthAssessment.STATUS_CANCELLED,
        ):
            raise ValidationException(
                f"Cannot submit answers to a {assessment.status} assessment."
            )

        question_id = data["question_id"]
        question = AnswerService._verify_question_applicable(assessment, question_id)

        # Duplicate answer prevention
        existing = AssessmentAnswer.query.filter_by(
            assessment_id=assessment_id,
            question_id=question_id,
        ).first()
        if existing:
            raise ConflictException(
                "An answer for this question has already been submitted. "
                "Use PUT to update it."
            )

        # Resolve and validate selected option if provided
        triggered_emergency = False
        selected_option_id = data.get("selected_option_id")
        selected_option = None

        if selected_option_id:
            selected_option = db.session.get(FollowUpQuestionOption, selected_option_id)
            if not selected_option:
                raise NotFoundException(
                    f"Option '{selected_option_id}' not found."
                )
            if selected_option.question_id != question_id:
                raise ValidationException(
                    "The selected option does not belong to the specified question."
                )
            triggered_emergency = selected_option.emergency_flag

        # Validate answer type alignment
        AnswerService._validate_answer_type(question, data, selected_option)

        answer = AssessmentAnswer(
            assessment_id=assessment_id,
            question_id=question_id,
            selected_option_id=selected_option_id,
            answer_text=data.get("answer_text"),
            numeric_value=data.get("numeric_value"),
            boolean_value=data.get("boolean_value"),
            triggered_emergency=triggered_emergency,
        )
        db.session.add(answer)
        db.session.commit()

        return answer.to_dict(include_question=True)

    @staticmethod
    def _validate_answer_type(
        question: FollowUpQuestion,
        data: Dict[str, Any],
        selected_option: Optional[FollowUpQuestionOption],
    ) -> None:
        """Validate that the answer value matches the question type."""
        qtype = question.question_type

        if qtype == FollowUpQuestion.TYPE_YES_NO:
            if data.get("boolean_value") is None and not selected_option:
                raise ValidationException(
                    "Yes/No questions require a 'boolean_value' or 'selected_option_id'."
                )

        elif qtype in (
            FollowUpQuestion.TYPE_SINGLE_CHOICE,
            FollowUpQuestion.TYPE_MULTIPLE_CHOICE,
        ):
            if not selected_option:
                raise ValidationException(
                    f"Choice questions require a valid 'selected_option_id'."
                )

        elif qtype == FollowUpQuestion.TYPE_NUMBER:
            if data.get("numeric_value") is None:
                raise ValidationException(
                    "Number questions require a 'numeric_value'."
                )

        elif qtype == FollowUpQuestion.TYPE_TEXT:
            if not data.get("answer_text"):
                raise ValidationException(
                    "Text questions require a non-empty 'answer_text'."
                )

    @staticmethod
    def get_answers(assessment_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Return all answers submitted for an assessment.

        Args:
            assessment_id: UUID of the assessment.
            user_id: Authenticated user's ID (for ownership check).

        Returns:
            List of serialized AssessmentAnswer dicts.
        """
        assessment = AnswerService._verify_assessment_and_ownership(assessment_id, user_id)
        answers = AssessmentAnswer.query.filter_by(
            assessment_id=assessment.id
        ).order_by(AssessmentAnswer.created_at.asc()).all()
        return [a.to_dict(include_question=True) for a in answers]

    @staticmethod
    def get_question_state(assessment_id: str, user_id: str) -> Dict[str, Any]:
        """Return the current progress and state of questions for an assessment.

        Returns:
            Dict containing:
                - progress: answered/total counts
                - emergency_flags: list of triggered emergency strings
                - next_questions: next batch of recommended questions
                - is_ready_for_completion: whether enough data is collected
                - safety_message: medical disclaimer
        """
        assessment = AnswerService._verify_assessment_and_ownership(assessment_id, user_id)
        return DynamicQuestionService.get_next_questions(assessment, batch_size=5)

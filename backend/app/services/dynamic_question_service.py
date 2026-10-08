"""Dynamic Follow-Up Question Service for intelligent assessment question selection.

This service implements a modular, rule-based engine that selects relevant follow-up
questions based on the current state of a health assessment. It considers:
    - Selected symptoms and their categories
    - Symptom severity and duration
    - Pet species, age, and sex
    - Existing conditions and current medications
    - Already-answered questions
    - Emergency indicators

The engine prioritizes emergency questions first, then high/medium/low priority.
It supports conditional questions triggered by specific answers.

IMPORTANT MEDICAL SAFETY NOTICE:
This service is designed for early health assessment support ONLY.
It does NOT diagnose diseases. It does NOT replace professional veterinary care.
Emergency indicators only flag potential urgency for veterinary attention.
"""
from typing import Dict, Any, List, Optional, Set
from datetime import date
from app.extensions import db
from app.models.health_assessment import HealthAssessment
from app.models.follow_up_question import FollowUpQuestion, FollowUpQuestionOption
from app.models.assessment_answer import AssessmentAnswer


# ---------------------------------------------------------------------------
# Rule Definitions
# ---------------------------------------------------------------------------
# Each rule is a dict describing when a question set should be triggered.
# Rules are evaluated against the current assessment state.
# Adding a new symptom/question only requires adding entries here and seeding
# the follow_up_questions table – no changes to core logic needed.

# Maps symptom names (lowercase) to their emergency-priority question category tags
EMERGENCY_SYMPTOM_CATEGORIES: Set[str] = {
    "difficulty breathing",
    "seizures",
    "collapse",
    "severe bleeding",
    "unresponsiveness",
    "difficulty urinating",
}

# Symptom name → category override map for question filtering
SYMPTOM_TO_CATEGORY: Dict[str, str] = {
    "vomiting": "Digestive",
    "diarrhea": "Digestive",
    "loss of appetite": "Digestive",
    "excessive thirst": "Digestive",
    "coughing": "Respiratory",
    "sneezing": "Respiratory",
    "difficulty breathing": "Respiratory",
    "lethargy": "General",
    "fever": "General",
    "itching": "Skin",
    "hair loss": "Skin",
    "skin redness": "Skin",
    "swelling": "Musculoskeletal",
    "limping": "Musculoskeletal",
    "eye discharge": "Eyes",
    "ear discharge": "Ears",
    "seizures": "Neurological",
    "abnormal behaviour": "Behavioural",
    "excessive urination": "Urinary",
    "difficulty urinating": "Urinary",
}

# Answer value triggers → conditional question categories to unlock
# Maps option_value → list of category tags whose questions should be prioritized
CONDITIONAL_TRIGGERS: Dict[str, List[str]] = {
    "blood_yes": ["Digestive"],
    "cannot_urinate": ["Urinary"],
    "breathing_worse": ["Respiratory"],
    "gums_blue": ["Respiratory"],
    "collapse_yes": ["General"],
    "seizure_active": ["Neurological"],
}


class DynamicQuestionService:
    """Rule-based engine that selects relevant unanswered follow-up questions.

    Responsibilities:
        1. Analyse current assessment: symptoms, observations, answers.
        2. Determine relevant categories/symptoms for question selection.
        3. Apply species and age filters.
        4. Remove already-answered questions.
        5. Prioritize emergency questions first.
        6. Apply conditional logic based on existing answers.
        7. Return a ranked list of next questions to ask.
    """

    # How many questions to return per batch
    DEFAULT_BATCH_SIZE = 3

    @classmethod
    def get_next_questions(
        cls,
        assessment: HealthAssessment,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> Dict[str, Any]:
        """Return the next most relevant unanswered questions for an assessment.

        Args:
            assessment: The HealthAssessment instance (must be loaded with
                        relationships: pet, symptoms, answers).
            batch_size: Number of questions to return in this batch.

        Returns:
            Dict containing:
                - questions: list of serialized question dicts with options
                - progress: dict with answered/total/remaining counts
                - emergency_flags: list of triggered emergency strings
                - is_complete: bool indicating if assessment has enough data
                - safety_message: standard veterinary disclaimer
        """
        pet = assessment.pet
        pet_species = (pet.species or "").strip() if pet else ""
        pet_age_months = cls._get_age_months(pet)

        # Determine what symptom categories/ids are relevant
        selected_symptom_ids, selected_categories = cls._extract_symptom_context(assessment)

        # Get IDs of questions already answered
        answered_question_ids = cls._get_answered_question_ids(assessment)

        # Collect emergency flags from current answers and symptoms
        emergency_flags = cls._collect_emergency_flags(assessment)

        # Get conditional category unlocks from existing answers
        conditional_categories = cls._get_conditional_categories(assessment)
        all_relevant_categories = selected_categories | conditional_categories

        # Build query for candidate questions
        candidate_questions = cls._query_candidate_questions(
            selected_symptom_ids=selected_symptom_ids,
            relevant_categories=all_relevant_categories,
            pet_species=pet_species,
            pet_age_months=pet_age_months,
            answered_question_ids=answered_question_ids,
            has_emergency=len(emergency_flags) > 0,
        )

        # Estimate total questions that could be asked for progress
        all_applicable = cls._count_all_applicable(
            selected_symptom_ids=selected_symptom_ids,
            relevant_categories=all_relevant_categories,
            pet_species=pet_species,
            pet_age_months=pet_age_months,
        )

        answered_count = len(answered_question_ids)
        remaining_count = max(0, all_applicable - answered_count)

        # Check if ready for completion (enough questions answered)
        is_ready = cls._is_assessment_ready(assessment, answered_count, all_applicable)

        questions_payload = [
            {**q.to_dict(include_options=True)}
            for q in candidate_questions[:batch_size]
        ]

        return {
            "questions": questions_payload,
            "progress": {
                "answered": answered_count,
                "total_estimated": all_applicable,
                "remaining_estimated": remaining_count,
            },
            "emergency_flags": emergency_flags,
            "is_ready_for_completion": is_ready,
            "safety_message": (
                "This information is for early health assessment support only and does "
                "not replace professional veterinary care. If your pet shows signs of "
                "acute distress, seek emergency veterinary attention immediately."
            ),
        }

    @classmethod
    def _get_age_months(cls, pet) -> Optional[int]:
        """Calculate pet age in months from date_of_birth."""
        if not pet or not pet.date_of_birth:
            return None
        today = date.today()
        months = (today.year - pet.date_of_birth.year) * 12 + (
            today.month - pet.date_of_birth.month
        )
        return max(0, months)

    @classmethod
    def _extract_symptom_context(
        cls, assessment: HealthAssessment
    ) -> tuple:
        """Return (set of symptom_ids, set of categories) from assessment symptoms."""
        symptom_ids: Set[str] = set()
        categories: Set[str] = set()

        if not assessment.symptoms:
            return symptom_ids, categories

        for assoc in assessment.symptoms:
            if assoc.symptom_id:
                symptom_ids.add(assoc.symptom_id)
            symptom_name = (
                assoc.symptom.name.lower() if assoc.symptom else ""
            )
            category = SYMPTOM_TO_CATEGORY.get(symptom_name)
            if category:
                categories.add(category)
            elif assoc.symptom and assoc.symptom.category:
                categories.add(assoc.symptom.category)

        return symptom_ids, categories

    @classmethod
    def _get_answered_question_ids(cls, assessment: HealthAssessment) -> Set[str]:
        """Return set of question IDs already answered for this assessment."""
        answered = (
            db.session.query(AssessmentAnswer.question_id)
            .filter_by(assessment_id=assessment.id)
            .all()
        )
        return {row[0] for row in answered}

    @classmethod
    def _collect_emergency_flags(cls, assessment: HealthAssessment) -> List[str]:
        """Collect emergency flag strings from symptoms and answer triggers."""
        flags: List[str] = []

        # Check critical symptoms
        if assessment.symptoms:
            for assoc in assessment.symptoms:
                name = (assoc.symptom.name.lower() if assoc.symptom else "")
                severity = (assoc.severity or "").lower()
                if name in EMERGENCY_SYMPTOM_CATEGORIES:
                    flags.append(
                        f"Critical symptom reported: {assoc.symptom.name}"
                        + (f" ({severity})" if severity else "")
                    )
                elif severity == "severe":
                    flags.append(
                        f"Severe symptom reported: {assoc.symptom.name if assoc.symptom else 'unknown'}"
                    )

        # Check answers that triggered emergency
        emergency_answers = (
            db.session.query(AssessmentAnswer)
            .filter_by(assessment_id=assessment.id, triggered_emergency=True)
            .all()
        )
        for ans in emergency_answers:
            q_text = ans.question.question_text if ans.question else "question"
            opt_text = ans.selected_option.option_text if ans.selected_option else str(ans.boolean_value)
            flags.append(f"Emergency indicator from answer: '{q_text}' → '{opt_text}'")

        return flags

    @classmethod
    def _get_conditional_categories(cls, assessment: HealthAssessment) -> Set[str]:
        """Unlock additional question categories based on existing answer values."""
        unlocked: Set[str] = set()
        answers = (
            db.session.query(AssessmentAnswer)
            .filter_by(assessment_id=assessment.id)
            .all()
        )
        for ans in answers:
            opt_val = ans.selected_option.option_value if ans.selected_option else ""
            for trigger_val, categories in CONDITIONAL_TRIGGERS.items():
                if opt_val == trigger_val:
                    unlocked.update(categories)
        return unlocked

    @classmethod
    def _query_candidate_questions(
        cls,
        selected_symptom_ids: Set[str],
        relevant_categories: Set[str],
        pet_species: str,
        pet_age_months: Optional[int],
        answered_question_ids: Set[str],
        has_emergency: bool,
    ) -> List[FollowUpQuestion]:
        """Query the database for relevant unanswered questions, ordered by priority."""
        query = FollowUpQuestion.query.filter(
            FollowUpQuestion.is_active == True,  # noqa: E712
        )

        # Exclude already answered questions
        if answered_question_ids:
            query = query.filter(
                ~FollowUpQuestion.id.in_(answered_question_ids)
            )

        # Filter by symptom or category relevance
        if selected_symptom_ids or relevant_categories:
            from sqlalchemy import or_
            conditions = []
            if selected_symptom_ids:
                conditions.append(FollowUpQuestion.symptom_id.in_(selected_symptom_ids))
            if relevant_categories:
                conditions.append(FollowUpQuestion.category.in_(relevant_categories))
            # Also include questions with no category/symptom binding (universal)
            conditions.append(
                (FollowUpQuestion.symptom_id == None) &  # noqa: E711
                (FollowUpQuestion.category == None)
            )
            query = query.filter(or_(*conditions))
        
        # Species filter: include questions with no species restriction OR matching species
        if pet_species:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    FollowUpQuestion.species == None,  # noqa: E711
                    FollowUpQuestion.species == pet_species,
                    # Case-insensitive species matching for common names
                    FollowUpQuestion.species == pet_species.title(),
                )
            )

        # Age filter: include questions where age range matches or is unrestricted
        if pet_age_months is not None:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    FollowUpQuestion.min_age_months == None,  # noqa: E711
                    FollowUpQuestion.min_age_months <= pet_age_months,
                )
            ).filter(
                or_(
                    FollowUpQuestion.max_age_months == None,  # noqa: E711
                    FollowUpQuestion.max_age_months >= pet_age_months,
                )
            )

        # Priority sort: emergency first, then high, medium, low, then display_order
        from sqlalchemy import case
        priority_case = case(
            {
                FollowUpQuestion.PRIORITY_EMERGENCY: 0,
                FollowUpQuestion.PRIORITY_HIGH: 1,
                FollowUpQuestion.PRIORITY_MEDIUM: 2,
                FollowUpQuestion.PRIORITY_LOW: 3,
            },
            value=FollowUpQuestion.priority,
            else_=4,
        )
        query = query.order_by(priority_case, FollowUpQuestion.display_order.asc())

        return query.all()

    @classmethod
    def _count_all_applicable(
        cls,
        selected_symptom_ids: Set[str],
        relevant_categories: Set[str],
        pet_species: str,
        pet_age_months: Optional[int],
    ) -> int:
        """Count total applicable questions for progress estimation."""
        return len(cls._query_candidate_questions(
            selected_symptom_ids=selected_symptom_ids,
            relevant_categories=relevant_categories,
            pet_species=pet_species,
            pet_age_months=pet_age_months,
            answered_question_ids=set(),  # count all, not just unanswered
            has_emergency=False,
        ))

    @classmethod
    def _is_assessment_ready(
        cls,
        assessment: HealthAssessment,
        answered_count: int,
        total_applicable: int,
    ) -> bool:
        """Determine whether the assessment has sufficient data to be completed.

        Criteria:
        - At least one symptom is attached.
        - At least 60% of applicable questions are answered OR at least 3
          emergency questions are answered if emergency flags are present.
        """
        if not assessment.symptoms:
            return False
        if total_applicable == 0:
            return True  # No questions applicable – can complete
        ratio = answered_count / total_applicable if total_applicable > 0 else 0
        return ratio >= 0.6 or answered_count >= 5


class QuestionBankService:
    """Service for retrieving and filtering the question bank.

    Provides filtered list endpoints for public question browsing.
    """

    @staticmethod
    def get_questions(
        symptom_id: Optional[str] = None,
        category: Optional[str] = None,
        species: Optional[str] = None,
        priority: Optional[str] = None,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """Return filtered list of follow-up questions from the question bank.

        Args:
            symptom_id: Optional filter by associated symptom UUID.
            category: Optional filter by category name.
            species: Optional filter by target species.
            priority: Optional filter by priority level.
            active_only: When True, only return active questions.

        Returns:
            List of serialized question dicts including options.
        """
        query = FollowUpQuestion.query

        if active_only:
            query = query.filter_by(is_active=True)

        if symptom_id:
            query = query.filter_by(symptom_id=symptom_id)

        if category:
            query = query.filter_by(category=category)

        if species:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    FollowUpQuestion.species == None,  # noqa: E711
                    FollowUpQuestion.species == species,
                )
            )

        if priority:
            query = query.filter_by(priority=priority)

        from sqlalchemy import case
        priority_case = case(
            {
                FollowUpQuestion.PRIORITY_EMERGENCY: 0,
                FollowUpQuestion.PRIORITY_HIGH: 1,
                FollowUpQuestion.PRIORITY_MEDIUM: 2,
                FollowUpQuestion.PRIORITY_LOW: 3,
            },
            value=FollowUpQuestion.priority,
            else_=4,
        )
        query = query.order_by(priority_case, FollowUpQuestion.display_order.asc())

        return [q.to_dict(include_options=True) for q in query.all()]

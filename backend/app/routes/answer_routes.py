"""Routes for dynamic follow-up question sessions and answer submission.

All assessment-specific endpoints require JWT authentication.

Endpoints:
    GET  /api/v1/assessments/<id>/next-questions
    POST /api/v1/assessments/<id>/answers
    GET  /api/v1/assessments/<id>/answers
    GET  /api/v1/assessments/<id>/question-state
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.response import success_response
from app.services.answer_service import AnswerService
from app.services.dynamic_question_service import DynamicQuestionService
from app.services.assessment_service import AssessmentService
from app.schemas.question_schema import answer_submit_schema

answer_bp = Blueprint("answers", __name__, url_prefix="/assessments")


@answer_bp.route("/<string:assessment_id>/next-questions", methods=["GET"])
@jwt_required()
def get_next_questions(assessment_id: str):
    """Return the next most relevant unanswered questions for an assessment.

    Dynamically selects questions based on:
    - Selected symptoms and their categories
    - Pet species and age
    - Already-answered questions
    - Emergency indicators triggered by previous answers

    Emergency-related questions are prioritized over routine ones.

    Returns:
        200: Dict containing next questions batch, progress stats, emergency flags.
        401: Missing or invalid token.
        403: Assessment belongs to another user.
        404: Assessment not found.

    Safety Note:
        These questions are for health assessment support only.
        They do NOT constitute veterinary medical advice or diagnosis.
    """
    user_id = get_jwt_identity()
    assessment = AssessmentService._verify_assessment_ownership(assessment_id, user_id)

    batch_size = request.args.get("batch_size", 3, type=int)
    batch_size = max(1, min(batch_size, 10))  # Clamp to 1–10

    result = DynamicQuestionService.get_next_questions(assessment, batch_size=batch_size)

    return success_response(
        data=result,
        message="Next recommended questions retrieved",
        status_code=200,
    )


@answer_bp.route("/<string:assessment_id>/answers", methods=["POST"])
@jwt_required()
def submit_answer(assessment_id: str):
    """Submit an answer to a follow-up question for an assessment.

    Validates:
    - Assessment ownership.
    - Question applicability to this assessment context.
    - No duplicate answers (one per question per assessment).
    - Option belongs to the specified question.
    - Answer value matches question type.

    Body:
        question_id        (str, required): UUID of the question to answer.
        selected_option_id (str, optional): UUID of the selected option (for choice questions).
        answer_text        (str, optional): Text answer (for text questions).
        numeric_value      (float, optional): Numeric answer (for number questions).
        boolean_value      (bool, optional): True/False (for yes_no questions).

    Returns:
        201: Submitted answer with question details.
        400: Invalid request body.
        401: Unauthorized.
        403: Forbidden (wrong user).
        404: Assessment or question not found.
        409: Answer already submitted for this question.
        422: Validation errors.
    """
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    validated_data = answer_submit_schema.load(payload)

    result = AnswerService.submit_answer(
        assessment_id=assessment_id,
        user_id=user_id,
        data=validated_data,
    )

    return success_response(
        data=result,
        message="Answer submitted successfully",
        status_code=201,
    )


@answer_bp.route("/<string:assessment_id>/answers", methods=["GET"])
@jwt_required()
def get_answers(assessment_id: str):
    """Return all answers submitted for an assessment.

    Returns:
        200: List of answers with question details.
        401: Unauthorized.
        403: Forbidden (wrong user).
        404: Assessment not found.
    """
    user_id = get_jwt_identity()
    answers = AnswerService.get_answers(assessment_id=assessment_id, user_id=user_id)

    return success_response(
        data={
            "answers": answers,
            "total": len(answers),
        },
        message="Assessment answers retrieved successfully",
        status_code=200,
    )


@answer_bp.route("/<string:assessment_id>/question-state", methods=["GET"])
@jwt_required()
def get_question_state(assessment_id: str):
    """Return the current question progress state for an assessment.

    Returns:
        - progress: { answered, total_estimated, remaining_estimated }
        - emergency_flags: list of triggered emergency indicator strings
        - next_questions: next batch of recommended questions
        - is_ready_for_completion: whether enough data is collected
        - safety_message: veterinary safety disclaimer

    Returns:
        200: Question state summary.
        401: Unauthorized.
        403: Forbidden (wrong user).
        404: Assessment not found.
    """
    user_id = get_jwt_identity()
    state = AnswerService.get_question_state(assessment_id=assessment_id, user_id=user_id)

    return success_response(
        data=state,
        message="Question state retrieved successfully",
        status_code=200,
    )

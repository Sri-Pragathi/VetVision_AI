"""Routes for the follow-up question bank (public browsing endpoint).

GET /api/v1/questions
    Returns available follow-up questions with optional filters:
    - symptom_id, category, species, priority
"""
from flask import Blueprint, request
from app.api.response import success_response
from app.services.dynamic_question_service import QuestionBankService
from app.schemas.question_schema import question_filter_schema

question_bp = Blueprint("questions", __name__, url_prefix="/questions")


@question_bp.route("", methods=["GET"])
def list_questions():
    """Return available follow-up questions from the question bank.

    Query Parameters:
        symptom_id (str): Filter by specific symptom UUID.
        category   (str): Filter by symptom category name.
        species    (str): Filter by target species.
        priority   (str): Filter by priority level (emergency/high/medium/low).

    Returns:
        200: List of follow-up questions with their options.
        422: Validation error for invalid filter values.

    Public endpoint – no authentication required (question bank is read-only metadata).
    """
    raw_params = {
        "symptom_id": request.args.get("symptom_id"),
        "category": request.args.get("category"),
        "species": request.args.get("species"),
        "priority": request.args.get("priority"),
    }
    # Remove None values so marshmallow uses load_default
    params = {k: v for k, v in raw_params.items() if v is not None}
    filters = question_filter_schema.load(params)

    questions = QuestionBankService.get_questions(
        symptom_id=filters.get("symptom_id"),
        category=filters.get("category"),
        species=filters.get("species"),
        priority=filters.get("priority"),
    )

    return success_response(
        data={
            "questions": questions,
            "total": len(questions),
        },
        message="Follow-up questions retrieved successfully",
        status_code=200,
    )

"""Guidance Assistant API Routes for interactive owner support."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.guidance_service import GuidanceAssistantService
from app.utils.error_handlers import ValidationException

guidance_bp = Blueprint("guidance", __name__, url_prefix="/guidance")


@guidance_bp.route("/quick-questions", methods=["GET"])
def get_quick_questions():
    """Get curated quick question templates for pet owners."""
    questions = GuidanceAssistantService.get_quick_questions()
    return jsonify({
        "status": "success",
        "data": {
            "questions": questions
        }
    }), 200


@guidance_bp.route("/ask", methods=["POST"])
@jwt_required(optional=True)
def ask_assistant():
    """Ask VetVision AI a supportive pet care question."""
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}

    question = payload.get("question")
    pet_id = payload.get("pet_id")
    assessment_id = payload.get("assessment_id")

    if not question or not str(question).strip():
        raise ValidationException("Field 'question' is required.")

    result = GuidanceAssistantService.ask(
        user_id=user_id,
        question=str(question).strip(),
        pet_id=pet_id,
        assessment_id=assessment_id,
    )

    return jsonify({
        "status": "success",
        "data": result
    }), 200

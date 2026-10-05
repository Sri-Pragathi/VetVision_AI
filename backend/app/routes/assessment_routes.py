"""Assessment endpoints for managing health check intake sessions."""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.response import success_response
from app.services.assessment_service import AssessmentService
from app.services.ai_data_service import AiDataPreparationService
from app.services.emergency_service import EmergencyAssessmentService
from app.schemas.assessment_schema import (
    assessment_status_update_schema,
    assessment_symptom_create_schema,
    assessment_symptom_update_schema,
    health_observation_schema,
    assessment_note_create_schema,
)

assessment_bp = Blueprint("assessments", __name__, url_prefix="/assessments")


@assessment_bp.route("/<string:assessment_id>", methods=["GET"])
@jwt_required()
def get_assessment(assessment_id: str):
    """Retrieve details of a single assessment owned by the authenticated user."""
    user_id = get_jwt_identity()
    assessment = AssessmentService.get_assessment_by_id(
        assessment_id=assessment_id, user_id=user_id
    )
    return success_response(
        data=assessment,
        message="Health assessment retrieved successfully",
        status_code=200,
    )


@assessment_bp.route("/<string:assessment_id>", methods=["PUT"])
@jwt_required()
def update_assessment_status(assessment_id: str):
    """Update assessment lifecycle status."""
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    validated_data = assessment_status_update_schema.load(payload)
    updated = AssessmentService.update_assessment_status(
        assessment_id=assessment_id,
        user_id=user_id,
        new_status=validated_data["status"],
    )
    return success_response(
        data=updated,
        message=f"Assessment status updated to {validated_data['status']}",
        status_code=200,
    )


@assessment_bp.route("/<string:assessment_id>", methods=["DELETE"])
@jwt_required()
def delete_assessment(assessment_id: str):
    """Delete an assessment session and associated records."""
    user_id = get_jwt_identity()
    AssessmentService.delete_assessment(
        assessment_id=assessment_id, user_id=user_id
    )
    return success_response(
        data=None,
        message="Health assessment deleted successfully",
        status_code=200,
    )


@assessment_bp.route("/<string:assessment_id>/symptoms", methods=["POST"])
@jwt_required()
def add_symptom(assessment_id: str):
    """Attach a clinical symptom to the assessment."""
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    validated_data = assessment_symptom_create_schema.load(payload)
    result = AssessmentService.add_symptom_to_assessment(
        assessment_id=assessment_id,
        user_id=user_id,
        data=validated_data,
    )
    return success_response(
        data=result,
        message="Symptom added to health assessment",
        status_code=201,
    )


@assessment_bp.route("/<string:assessment_id>/symptoms/<string:symptom_id>", methods=["PUT"])
@jwt_required()
def update_symptom(assessment_id: str, symptom_id: str):
    """Update severity, duration, or notes of an attached symptom."""
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    validated_data = assessment_symptom_update_schema.load(payload)
    result = AssessmentService.update_assessment_symptom(
        assessment_id=assessment_id,
        symptom_id=symptom_id,
        user_id=user_id,
        data=validated_data,
    )
    return success_response(
        data=result,
        message="Symptom updated successfully",
        status_code=200,
    )


@assessment_bp.route("/<string:assessment_id>/symptoms/<string:symptom_id>", methods=["DELETE"])
@jwt_required()
def remove_symptom(assessment_id: str, symptom_id: str):
    """Detach a symptom from the assessment."""
    user_id = get_jwt_identity()
    AssessmentService.remove_assessment_symptom(
        assessment_id=assessment_id,
        symptom_id=symptom_id,
        user_id=user_id,
    )
    return success_response(
        data=None,
        message="Symptom removed from health assessment",
        status_code=200,
    )


@assessment_bp.route("/<string:assessment_id>/observations", methods=["PUT"])
@jwt_required()
def upsert_observations(assessment_id: str):
    """Create or update structured clinical observations for the assessment."""
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    validated_data = health_observation_schema.load(payload)
    result = AssessmentService.upsert_observations(
        assessment_id=assessment_id,
        user_id=user_id,
        data=validated_data,
    )
    return success_response(
        data=result,
        message="Observations recorded successfully",
        status_code=200,
    )


@assessment_bp.route("/<string:assessment_id>/notes", methods=["POST"])
@jwt_required()
def add_note(assessment_id: str):
    """Append a clinical or owner free-text note to the assessment."""
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    validated_data = assessment_note_create_schema.load(payload)
    result = AssessmentService.add_note(
        assessment_id=assessment_id,
        user_id=user_id,
        note_text=validated_data["note"],
    )
    return success_response(
        data=result,
        message="Note added to health assessment",
        status_code=201,
    )


@assessment_bp.route("/<string:assessment_id>/ai-data", methods=["GET"])
@jwt_required()
def get_ai_data_payload(assessment_id: str):
    """Retrieve structured AI-ready payload and emergency triage risk evaluation."""
    user_id = get_jwt_identity()
    assessment_obj = AssessmentService._verify_assessment_ownership(assessment_id, user_id)
    ai_payload = AiDataPreparationService.prepare_ai_payload(assessment_obj)
    emergency_evaluation = EmergencyAssessmentService.evaluate_payload(ai_payload)

    return success_response(
        data={
            "ai_input": ai_payload,
            "emergency_screening": emergency_evaluation,
        },
        message="AI-ready data and emergency triage evaluated successfully",
        status_code=200,
    )

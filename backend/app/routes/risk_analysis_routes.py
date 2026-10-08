"""Routes for AI health risk analysis engine endpoints.

Endpoints:
    POST /api/v1/assessments/<assessment_id>/risk-analysis
    GET  /api/v1/assessments/<assessment_id>/risk-analysis
"""
from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.response import success_response
from app.services.risk_analysis_service import RiskAnalysisService

risk_analysis_bp = Blueprint("risk_analysis", __name__, url_prefix="/assessments")


@risk_analysis_bp.route("/<string:assessment_id>/risk-analysis", methods=["POST"])
@jwt_required()
def run_risk_analysis(assessment_id: str):
    """Execute AI health risk analysis on an assessment.

    Evaluates complete multi-modal assessment context:
    - Pet baseline & vulnerability (species, age, chronic conditions)
    - Symptom severity & duration
    - Physiological & behavioral observations
    - Dynamic follow-up question responses
    - Emergency indicators (hard-stop rule)

    Guarantees:
    - Explainable factor breakdown
    - Emergency priority enforcement
    - Safe veterinary disclaimers (no definitive diagnosis)
    - Idempotent / upserted analysis record

    Returns:
        200: Computed risk analysis with level, score, factors, and recommendation.
        400/422: Validation error (e.g. no symptoms, cancelled assessment).
        401: Unauthorized (missing or invalid token).
        403: Forbidden (assessment belongs to another user).
        404: Assessment not found.
    """
    user_id = get_jwt_identity()
    result = RiskAnalysisService.analyze_assessment(
        assessment_id=assessment_id,
        user_id=user_id,
    )

    return success_response(
        data=result,
        message="AI health risk analysis completed successfully",
        status_code=200,
    )


@risk_analysis_bp.route("/<string:assessment_id>/risk-analysis", methods=["GET"])
@jwt_required()
def get_risk_analysis(assessment_id: str):
    """Retrieve the latest stored AI health risk analysis for an assessment.

    Returns:
        200: Stored risk analysis.
        401: Unauthorized.
        403: Forbidden (wrong user).
        404: Assessment not found or no risk analysis generated yet.
    """
    user_id = get_jwt_identity()
    result = RiskAnalysisService.get_assessment_risk_analysis(
        assessment_id=assessment_id,
        user_id=user_id,
    )

    return success_response(
        data=result,
        message="AI health risk analysis retrieved successfully",
        status_code=200,
    )

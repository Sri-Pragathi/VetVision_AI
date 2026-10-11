"""Doctor clinical review endpoints for managing queue, assessments, and diagnostic reviews."""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.response import success_response
from app.utils.security import doctor_required
from app.services.doctor_service import DoctorService
from app.schemas.doctor_review_schema import DoctorReviewCreateSchema

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")
review_create_schema = DoctorReviewCreateSchema()


@doctor_bp.route("/cases", methods=["GET"])
@jwt_required()
@doctor_required()
def get_clinical_cases():
    """Retrieve paginated clinical intake cases for medical review queue."""
    triage_level = request.args.get("triage_level")
    review_status = request.args.get("review_status")
    search = request.args.get("search")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    result = DoctorService.list_clinical_cases(
        triage_level=triage_level,
        review_status=review_status,
        search=search,
        page=page,
        per_page=per_page,
    )
    return success_response(
        data=result,
        message="Clinical cases retrieved successfully",
        status_code=200,
    )


@doctor_bp.route("/cases/<string:assessment_id>", methods=["GET"])
@jwt_required()
@doctor_required()
def get_case_detail(assessment_id: str):
    """Retrieve full clinical case record including history, AI risk analysis, and reviews."""
    case_data = DoctorService.get_clinical_case(assessment_id)
    return success_response(
        data=case_data,
        message="Clinical case details retrieved successfully",
        status_code=200,
    )


@doctor_bp.route("/cases/<string:assessment_id>/review", methods=["POST", "PUT"])
@jwt_required()
@doctor_required()
def submit_case_review(assessment_id: str):
    """Submit or update veterinary clinical review, triage override, and notes."""
    doctor_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    payload["assessment_id"] = assessment_id
    validated_data = review_create_schema.load(payload)

    review = DoctorService.submit_doctor_review(
        assessment_id=assessment_id,
        doctor_id=doctor_id,
        review_data=validated_data,
    )
    return success_response(
        data=review,
        message="Doctor clinical review saved successfully",
        status_code=200,
    )

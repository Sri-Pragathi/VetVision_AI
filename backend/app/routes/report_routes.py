"""Routes for Veterinary Report & Explainable Health Summary endpoints.

Endpoints:
    POST /api/v1/assessments/<assessment_id>/reports
    GET  /api/v1/assessments/<assessment_id>/reports
    GET  /api/v1/reports/<report_id>
    GET  /api/v1/reports/<report_id>/html
"""
from flask import Blueprint, Response, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.response import success_response
from app.services.report_service import ReportService

# Blueprint for assessment-nested report endpoints
assessment_report_bp = Blueprint("assessment_reports", __name__, url_prefix="/assessments")

# Blueprint for direct report resource endpoints
report_bp = Blueprint("reports", __name__, url_prefix="/reports")


@assessment_report_bp.route("/<string:assessment_id>/reports", methods=["POST"])
@jwt_required()
def generate_report(assessment_id: str):
    """Generate an immutable, versioned report snapshot of an assessment.

    Gathers pet profile, assessment timeline, reported symptoms,
    adaptive follow-up Q&A, clinical observations, image analysis,
    risk factors, emergency status, and veterinary handoff.

    Returns:
        201: Report generated successfully.
        400/422: Validation error (e.g. cancelled, no symptoms).
        401: Unauthorized.
        403: Forbidden (wrong user).
        404: Assessment not found.
    """
    user_id = get_jwt_identity()
    report = ReportService.generate_assessment_report(
        assessment_id=assessment_id,
        user_id=user_id,
    )
    return success_response(
        data=report,
        message="Veterinary assessment report generated successfully",
        status_code=201,
    )


@assessment_report_bp.route("/<string:assessment_id>/reports", methods=["GET"])
@jwt_required()
def list_reports(assessment_id: str):
    """List all historical and active report snapshots for an assessment.

    Returns:
        200: List of report summaries.
        401: Unauthorized.
        403: Forbidden (wrong user).
        404: Assessment not found.
    """
    user_id = get_jwt_identity()
    reports = ReportService.get_assessment_reports(
        assessment_id=assessment_id,
        user_id=user_id,
    )
    return success_response(
        data=reports,
        message="Assessment reports retrieved successfully",
        status_code=200,
    )


@report_bp.route("/<string:report_id>", methods=["GET"])
@jwt_required()
def get_report(report_id: str):
    """Retrieve full structured report snapshot by ID.

    Supports content negotiation: if 'Accept: text/html' header is requested,
    renders the HTML report instead of JSON.

    Returns:
        200: Complete structured report payload (or HTML if requested).
        401: Unauthorized.
        403: Forbidden (wrong user).
        404: Report not found.
    """
    user_id = get_jwt_identity()
    accept_header = request.headers.get("Accept", "")
    if "text/html" in accept_header and "application/json" not in accept_header:
        html_content = ReportService.get_report_html(
            report_id=report_id,
            user_id=user_id,
        )
        return Response(html_content, mimetype="text/html", status=200)

    report = ReportService.get_report_by_id(
        report_id=report_id,
        user_id=user_id,
    )
    return success_response(
        data=report,
        message="Veterinary assessment report retrieved successfully",
        status_code=200,
    )


@report_bp.route("/<string:report_id>/html", methods=["GET"])
@jwt_required()
def get_report_html(report_id: str):
    """Render standalone, human-readable HTML document for viewing or printing.

    Returns:
        200: Text/HTML response.
        401: Unauthorized.
        403: Forbidden (wrong user).
        404: Report not found.
    """
    user_id = get_jwt_identity()
    html_content = ReportService.get_report_html(
        report_id=report_id,
        user_id=user_id,
    )
    return Response(html_content, mimetype="text/html", status=200)

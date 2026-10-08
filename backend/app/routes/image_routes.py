"""Routes for pet image upload, management, and computer-vision analysis.

Endpoints:
    POST   /api/v1/assessments/<assessment_id>/images
    GET    /api/v1/assessments/<assessment_id>/images
    GET    /api/v1/assessment-images/<image_id>
    POST   /api/v1/assessment-images/<image_id>/analyze
    GET    /api/v1/assessment-images/<image_id>/analysis
    DELETE /api/v1/assessment-images/<image_id>
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.response import success_response
from app.services.image_analysis_service import ImageAnalysisService
from app.utils.error_handlers import ValidationException

image_bp = Blueprint("images", __name__)


@image_bp.route("/assessments/<string:assessment_id>/images", methods=["POST"])
@jwt_required()
def upload_image(assessment_id: str):
    """Upload a pet photograph to an existing health assessment.

    Expects multipart/form-data with file field named 'image' or 'file'.
    Validates MIME type, file extension, file size, and image readability.
    """
    user_id = get_jwt_identity()

    # Look for uploaded file in 'image' or 'file' form fields
    file_obj = request.files.get("image") or request.files.get("file")
    if not file_obj:
        raise ValidationException(
            "No image file provided in upload request. Expected multipart field 'image' or 'file'."
        )

    result = ImageAnalysisService.upload_assessment_image(
        assessment_id=assessment_id,
        user_id=user_id,
        file_obj=file_obj,
    )

    return success_response(
        data=result,
        message="Pet image uploaded successfully",
        status_code=201,
    )


@image_bp.route("/assessments/<string:assessment_id>/images", methods=["GET"])
@jwt_required()
def list_assessment_images(assessment_id: str):
    """List all photographs attached to an assessment."""
    user_id = get_jwt_identity()
    images = ImageAnalysisService.get_assessment_images(
        assessment_id=assessment_id,
        user_id=user_id,
    )

    return success_response(
        data={
            "images": images,
            "total": len(images),
        },
        message="Assessment images retrieved successfully",
        status_code=200,
    )


@image_bp.route("/assessment-images/<string:image_id>", methods=["GET"])
@jwt_required()
def get_image_details(image_id: str):
    """Retrieve metadata, processing status, and observations for an image."""
    user_id = get_jwt_identity()
    image = ImageAnalysisService.get_image_by_id(
        image_id=image_id,
        user_id=user_id,
    )

    return success_response(
        data=image,
        message="Assessment image details retrieved successfully",
        status_code=200,
    )


@image_bp.route("/assessment-images/<string:image_id>/analyze", methods=["POST"])
@jwt_required()
def analyze_image(image_id: str):
    """Execute computer vision processing on an uploaded pet photograph.

    Evaluates:
    - Image quality gate (dimensions, lighting, contrast, blur)
    - Visual feature observations (erythema, color distribution)
    - Extensible adapter architecture for future validated models
    """
    user_id = get_jwt_identity()
    result = ImageAnalysisService.analyze_image(
        image_id=image_id,
        user_id=user_id,
    )

    return success_response(
        data=result,
        message="Computer vision analysis completed successfully",
        status_code=200,
    )


@image_bp.route("/assessment-images/<string:image_id>/analysis", methods=["GET"])
@jwt_required()
def get_image_analysis(image_id: str):
    """Retrieve structured computer vision analysis results and observations."""
    user_id = get_jwt_identity()
    result = ImageAnalysisService.get_image_analysis(
        image_id=image_id,
        user_id=user_id,
    )

    return success_response(
        data=result,
        message="Computer vision analysis retrieved successfully",
        status_code=200,
    )


@image_bp.route("/assessment-images/<string:image_id>", methods=["DELETE"])
@jwt_required()
def delete_image(image_id: str):
    """Delete an assessment photograph and its associated observations."""
    user_id = get_jwt_identity()
    ImageAnalysisService.delete_image(
        image_id=image_id,
        user_id=user_id,
    )

    return success_response(
        data=None,
        message="Assessment image deleted successfully",
        status_code=200,
    )

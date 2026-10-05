"""Health check endpoint."""
from flask import Blueprint
from app.api.response import success_response

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify backend service status."""
    return success_response(
        message="VetVision AI backend is running",
        status_code=200,
    )

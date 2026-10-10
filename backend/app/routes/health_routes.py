"""Health check endpoint with database connectivity status and liveness/readiness probes."""
from flask import Blueprint, current_app
from sqlalchemy import text
from app.extensions import db
from app.api.response import success_response, error_response

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint verifying backend service status and database connectivity."""
    db_status = "connected"
    is_healthy = True

    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        # Protect against exposing database credentials, host, or internal stack traces
        db_status = "disconnected"
        is_healthy = False

    payload = {
        "status": "healthy" if is_healthy else "unhealthy",
        "database": db_status,
        "environment": current_app.config.get("ENV", "development"),
    }

    if is_healthy:
        return success_response(
            data=payload,
            message="VetVision AI backend is running",
            status_code=200,
        )
    return error_response(
        message="VetVision AI backend is degraded or database unavailable",
        errors=payload,
        status_code=503,
    )


@health_bp.route("/health/live", methods=["GET"])
def liveness_check():
    """Liveness probe verifying that the application process is running."""
    return success_response(
        data={"status": "alive"},
        message="VetVision AI process is alive",
        status_code=200,
    )


@health_bp.route("/health/ready", methods=["GET"])
def readiness_check():
    """Readiness probe verifying that backend dependencies are operational."""
    return health_check()

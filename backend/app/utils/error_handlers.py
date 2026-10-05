"""Centralized error handling and custom exceptions for VetVision AI."""
import logging
from typing import Any, Dict, Optional
from flask import Flask, current_app
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException
from app.api.response import error_response
from app.extensions import jwt

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception."""
    status_code: int = 500
    message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        errors: Optional[Any] = None,
        status_code: Optional[int] = None,
    ):
        super().__init__(message or self.message)
        if message:
            self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.errors = errors


class BadRequestException(AppException):
    status_code = 400
    message = "Bad request"


class UnauthorizedException(AppException):
    status_code = 401
    message = "Unauthorized access"


class ForbiddenException(AppException):
    status_code = 403
    message = "Access forbidden"


class NotFoundException(AppException):
    status_code = 404
    message = "Resource not found"


class ConflictException(AppException):
    status_code = 409
    message = "Resource conflict"


class ValidationException(AppException):
    status_code = 422
    message = "Validation failed"


def register_error_handlers(app: Flask) -> None:
    """Register centralized error handlers with the Flask app."""

    @app.errorhandler(AppException)
    def handle_app_exception(err: AppException):
        return error_response(
            message=err.message,
            errors=err.errors,
            status_code=err.status_code,
        )

    @app.errorhandler(ValidationError)
    def handle_marshmallow_validation(err: ValidationError):
        return error_response(
            message="Validation failed",
            errors=err.messages,
            status_code=422,
        )

    @app.errorhandler(400)
    def handle_400(err):
        description = getattr(err, "description", "Bad request")
        return error_response(message=description, status_code=400)

    @app.errorhandler(401)
    def handle_401(err):
        description = getattr(err, "description", "Unauthorized")
        return error_response(message=description, status_code=401)

    @app.errorhandler(403)
    def handle_403(err):
        description = getattr(err, "description", "Forbidden")
        return error_response(message=description, status_code=403)

    @app.errorhandler(404)
    def handle_404(err):
        description = getattr(err, "description", "Resource not found")
        return error_response(message=description, status_code=404)

    @app.errorhandler(405)
    def handle_405(err):
        return error_response(message="Method not allowed", status_code=405)

    @app.errorhandler(409)
    def handle_409(err):
        description = getattr(err, "description", "Resource conflict")
        return error_response(message=description, status_code=409)

    @app.errorhandler(422)
    def handle_422(err):
        description = getattr(err, "description", "Unprocessable entity")
        return error_response(message=description, status_code=422)

    @app.errorhandler(HTTPException)
    def handle_http_exception(err: HTTPException):
        return error_response(
            message=err.description or "HTTP Error",
            status_code=err.code or 500,
        )

    @app.errorhandler(Exception)
    def handle_generic_exception(err: Exception):
        # Log stack trace internally without exposing to client
        app.logger.error(f"Unhandled exception: {err}", exc_info=True)
        return error_response(
            message="Internal server error. Please try again later.",
            status_code=500,
        )

    # JWT Error Loaders for consistent JSON structure
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return error_response(
            message="Token has expired. Please log in again.",
            status_code=401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        return error_response(
            message=f"Invalid authentication token: {error_string}",
            status_code=401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        return error_response(
            message="Authentication token is missing. Authorization header required.",
            status_code=401,
        )

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return error_response(
            message="Token has been revoked. Please log in again.",
            status_code=401,
        )

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return error_response(
            message="Fresh token required for this action.",
            status_code=401,
        )

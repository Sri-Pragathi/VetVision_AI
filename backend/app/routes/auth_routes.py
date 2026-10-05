"""Authentication endpoints for registration, login, token refresh, and logout."""
from flask import Blueprint, request
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from app.api.response import success_response
from app.schemas.auth_schema import register_schema, login_schema
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account."""
    payload = request.get_json(silent=True) or {}
    validated_data = register_schema.load(payload)
    result, _ = AuthService.register_user(validated_data)
    return success_response(
        data=result,
        message="User registered successfully",
        status_code=201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate an existing user and provide access/refresh tokens."""
    payload = request.get_json(silent=True) or {}
    validated_data = login_schema.load(payload)
    result, _ = AuthService.login_user(validated_data)
    return success_response(
        data=result,
        message="Login successful",
        status_code=200,
    )


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh an expired access token using a valid refresh token."""
    user_id = get_jwt_identity()
    result = AuthService.refresh_access_token(user_id)
    return success_response(
        data=result,
        message="Token refreshed successfully",
        status_code=200,
    )


@auth_bp.route("/logout", methods=["POST"])
@jwt_required(verify_type=False)
def logout():
    """Revoke the current JWT token (access or refresh)."""
    jwt_payload = get_jwt()
    jti = jwt_payload["jti"]
    token_type = jwt_payload["type"]
    AuthService.logout_token(jti=jti, token_type=token_type)
    return success_response(
        message="Successfully logged out",
        status_code=200,
    )


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Get the current authenticated user's profile."""
    user_id = get_jwt_identity()
    profile = AuthService.get_user_profile(user_id)
    return success_response(
        data=profile,
        message="User profile retrieved successfully",
        status_code=200,
    )

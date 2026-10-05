"""User endpoints for profile retrieval and update."""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.response import success_response
from app.schemas.user_schema import user_update_schema, user_profile_schema
from app.services.user_service import UserService

user_bp = Blueprint("users", __name__, url_prefix="/users")


@user_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """Retrieve current authenticated user's profile."""
    user_id = get_jwt_identity()
    user = UserService.get_user_by_id(user_id)
    return success_response(
        data=user.to_dict(),
        message="User profile retrieved successfully",
        status_code=200,
    )


@user_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_current_user():
    """Update current authenticated user's profile."""
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    validated_data = user_update_schema.load(payload)
    updated_user = UserService.update_user_profile(user_id, validated_data)
    return success_response(
        data=updated_user,
        message="User profile updated successfully",
        status_code=200,
    )

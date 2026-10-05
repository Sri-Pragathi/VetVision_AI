"""Pet endpoints for managing pet profiles with ownership security."""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.response import success_response
from app.schemas.pet_schema import pet_create_schema, pet_update_schema
from app.services.pet_service import PetService

pet_bp = Blueprint("pets", __name__, url_prefix="/pets")


@pet_bp.route("", methods=["POST"])
@jwt_required()
def create_pet():
    """Create a new pet for the authenticated user."""
    owner_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    validated_data = pet_create_schema.load(payload)
    new_pet = PetService.create_pet(owner_id=owner_id, data=validated_data)
    return success_response(
        data=new_pet,
        message="Pet created successfully",
        status_code=201,
    )


@pet_bp.route("", methods=["GET"])
@jwt_required()
def list_pets():
    """List all pets belonging exclusively to the authenticated user."""
    owner_id = get_jwt_identity()
    pets = PetService.get_user_pets(owner_id=owner_id)
    return success_response(
        data=pets,
        message="Pets retrieved successfully",
        status_code=200,
    )


@pet_bp.route("/<string:pet_id>", methods=["GET"])
@jwt_required()
def get_pet(pet_id: str):
    """Retrieve details of a specific pet owned by the authenticated user."""
    owner_id = get_jwt_identity()
    pet = PetService.get_pet_by_id(pet_id=pet_id, owner_id=owner_id)
    return success_response(
        data=pet.to_dict(),
        message="Pet retrieved successfully",
        status_code=200,
    )


@pet_bp.route("/<string:pet_id>", methods=["PUT"])
@jwt_required()
def update_pet(pet_id: str):
    """Update details of a specific pet owned by the authenticated user."""
    owner_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    validated_data = pet_update_schema.load(payload)
    updated_pet = PetService.update_pet(
        pet_id=pet_id,
        owner_id=owner_id,
        data=validated_data,
    )
    return success_response(
        data=updated_pet,
        message="Pet updated successfully",
        status_code=200,
    )


@pet_bp.route("/<string:pet_id>", methods=["DELETE"])
@jwt_required()
def delete_pet(pet_id: str):
    """Delete a specific pet owned by the authenticated user."""
    owner_id = get_jwt_identity()
    PetService.delete_pet(pet_id=pet_id, owner_id=owner_id)
    return success_response(
        data=None,
        message="Pet deleted successfully",
        status_code=200,
    )


@pet_bp.route("/<string:pet_id>/assessments", methods=["POST"])
@jwt_required()
def create_pet_assessment(pet_id: str):
    """Create a new health assessment session for the specified pet."""
    user_id = get_jwt_identity()
    from app.services.assessment_service import AssessmentService
    new_assessment = AssessmentService.create_assessment(
        pet_id=pet_id, user_id=user_id
    )
    return success_response(
        data=new_assessment,
        message="Health assessment session started successfully",
        status_code=201,
    )


@pet_bp.route("/<string:pet_id>/assessments", methods=["GET"])
@jwt_required()
def list_pet_assessments(pet_id: str):
    """List all health assessments for the specified pet."""
    user_id = get_jwt_identity()
    from app.services.assessment_service import AssessmentService
    assessments = AssessmentService.get_pet_assessments(
        pet_id=pet_id, user_id=user_id
    )
    return success_response(
        data=assessments,
        message="Health assessments retrieved successfully",
        status_code=200,
    )

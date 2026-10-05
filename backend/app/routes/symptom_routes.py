"""Symptom vocabulary endpoints."""
from flask import Blueprint, request
from app.api.response import success_response
from app.services.symptom_service import SymptomService

symptom_bp = Blueprint("symptoms", __name__, url_prefix="/symptoms")


@symptom_bp.route("", methods=["GET"])
def list_symptoms():
    """List available clinical symptoms with optional category filtering."""
    category = request.args.get("category")
    symptoms = SymptomService.get_all_symptoms(category=category)
    return success_response(
        data=symptoms,
        message="Symptoms retrieved successfully",
        status_code=200,
    )

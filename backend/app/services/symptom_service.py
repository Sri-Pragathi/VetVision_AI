"""Symptom vocabulary service for querying clinical symptoms."""
from typing import List, Dict, Any, Optional
from app.extensions import db
from app.models.symptom import Symptom
from app.utils.error_handlers import NotFoundException


class SymptomService:
    """Service for querying structured symptom vocabulary."""

    @staticmethod
    def get_all_symptoms(category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve all symptoms, optionally filtered by category (case-insensitive)."""
        query = Symptom.query
        if category:
            category_cleaned = category.strip()
            # Case-insensitive category match
            query = query.filter(Symptom.category.ilike(category_cleaned))
        
        symptoms = query.order_by(Symptom.category.asc(), Symptom.name.asc()).all()
        return [s.to_dict() for s in symptoms]

    @staticmethod
    def get_symptom_by_id(symptom_id: str) -> Symptom:
        """Fetch a specific symptom by ID or raise NotFoundException."""
        symptom = db.session.get(Symptom, symptom_id)
        if not symptom:
            raise NotFoundException(f"Symptom with ID '{symptom_id}' not found.")
        return symptom

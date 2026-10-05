"""Pet management service with strict ownership security enforcement."""
from typing import Dict, Any, List
from app.extensions import db
from app.models.pet import Pet
from app.utils.error_handlers import NotFoundException, ForbiddenException


class PetService:
    """Service handling pet records with strict owner isolation."""

    @staticmethod
    def create_pet(owner_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pet belonging exclusively to the specified owner."""
        pet = Pet(
            owner_id=owner_id,
            name=data["name"].strip(),
            species=data["species"].strip(),
            breed=data.get("breed"),
            sex=data.get("sex"),
            date_of_birth=data.get("date_of_birth"),
            weight=data.get("weight"),
            allergies=data.get("allergies"),
            existing_conditions=data.get("existing_conditions"),
            current_medications=data.get("current_medications"),
            vaccination_status=data.get("vaccination_status"),
        )
        db.session.add(pet)
        db.session.commit()
        return pet.to_dict()

    @staticmethod
    def get_user_pets(owner_id: str) -> List[Dict[str, Any]]:
        """Retrieve all pets owned by the specified user."""
        pets = (
            Pet.query.filter_by(owner_id=owner_id)
            .order_by(Pet.created_at.desc())
            .all()
        )
        return [pet.to_dict() for pet in pets]

    @staticmethod
    def get_pet_by_id(pet_id: str, owner_id: str) -> Pet:
        """Retrieve a specific pet ensuring strict owner verification.
        
        Raises NotFoundException if pet does not exist.
        Raises ForbiddenException if pet belongs to another user.
        """
        pet = db.session.get(Pet, pet_id)
        if not pet:
            raise NotFoundException("Pet not found.")
        
        # Enforce security ownership check
        if pet.owner_id != owner_id:
            raise ForbiddenException("You do not have permission to access this pet.")
            
        return pet

    @staticmethod
    def update_pet(pet_id: str, owner_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing pet after validating ownership."""
        pet = PetService.get_pet_by_id(pet_id=pet_id, owner_id=owner_id)

        # Update allowed fields if provided
        updatable_fields = [
            "name",
            "species",
            "breed",
            "sex",
            "date_of_birth",
            "weight",
            "allergies",
            "existing_conditions",
            "current_medications",
            "vaccination_status",
        ]

        for field in updatable_fields:
            if field in data:
                val = data[field]
                if isinstance(val, str):
                    val = val.strip()
                setattr(pet, field, val)

        db.session.commit()
        return pet.to_dict()

    @staticmethod
    def delete_pet(pet_id: str, owner_id: str) -> None:
        """Delete an existing pet after validating ownership."""
        pet = PetService.get_pet_by_id(pet_id=pet_id, owner_id=owner_id)
        db.session.delete(pet)
        db.session.commit()

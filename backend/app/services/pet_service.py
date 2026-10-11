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
            weight_unit=data.get("weight_unit") or "kg",
            photo_url=data.get("photo_url"),
            spayed_neutered=data.get("spayed_neutered"),
            allergies=data.get("allergies"),
            existing_conditions=data.get("existing_conditions"),
            current_medications=data.get("current_medications"),
            vaccination_status=data.get("vaccination_status"),
            vaccination_history=data.get("vaccination_history"),
            medical_history=data.get("medical_history"),
            notes=data.get("notes"),
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
            "weight_unit",
            "photo_url",
            "spayed_neutered",
            "allergies",
            "existing_conditions",
            "current_medications",
            "vaccination_status",
            "vaccination_history",
            "medical_history",
            "notes",
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

    @staticmethod
    def upload_pet_avatar(pet_id: str, owner_id: str, file_obj: Any) -> Dict[str, Any]:
        """Upload and associate an avatar image for a pet."""
        import io
        from PIL import Image
        from werkzeug.utils import secure_filename
        from app.services.storage_service import LocalStorageService
        from app.utils.error_handlers import ValidationException

        pet = PetService.get_pet_by_id(pet_id=pet_id, owner_id=owner_id)

        filename = secure_filename(getattr(file_obj, "filename", "avatar.jpg"))
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
        if ext not in ["jpg", "jpeg", "png", "webp"]:
            raise ValidationException(f"Invalid image format '{ext}'. Must be jpg, jpeg, png, or webp.")

        file_bytes = file_obj.read()
        if len(file_bytes) == 0:
            raise ValidationException("Avatar file is empty.")
        if len(file_bytes) > 10 * 1024 * 1024:
            raise ValidationException("Avatar file exceeds 10MB limit.")

        try:
            pil_img = Image.open(io.BytesIO(file_bytes))
            pil_img.verify()
        except Exception:
            raise ValidationException("File is corrupted or not a valid image.")

        storage = LocalStorageService()
        storage_rel_path = f"pets/{pet.id}/avatar.{ext}"
        storage.save_file(file_bytes, storage_rel_path)

        pet.photo_url = f"/api/v1/pets/{pet.id}/avatar"
        db.session.commit()
        return pet.to_dict()

    @staticmethod
    def get_pet_avatar(pet_id: str, user_id: str) -> tuple[str, str]:
        """Retrieve local filesystem path and MIME type for pet avatar with role authorization."""
        from app.models.user import User
        from app.services.storage_service import LocalStorageService

        pet = db.session.get(Pet, pet_id)
        if not pet:
            raise NotFoundException("Pet not found.")

        if pet.owner_id != user_id:
            raise ForbiddenException("You do not have permission to access this pet avatar.")

        storage = LocalStorageService()
        base_dir = storage.base_dir / "pets" / pet.id
        if not base_dir.is_dir():
            raise NotFoundException("Pet avatar not found.")

        files = list(base_dir.glob("avatar.*"))
        if not files:
            raise NotFoundException("Pet avatar not found.")

        target = files[0]
        ext = target.suffix.lstrip(".").lower()
        mime_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
        }
        return str(target), mime_map.get(ext, "image/jpeg")

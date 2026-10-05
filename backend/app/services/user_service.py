"""User profile management service."""
from typing import Dict, Any
from app.extensions import db
from app.models.user import User
from app.utils.error_handlers import NotFoundException, ConflictException


class UserService:
    """Service handling user profile operations."""

    @staticmethod
    def get_user_by_id(user_id: str) -> User:
        """Fetch user by ID or raise NotFoundException."""
        user = db.session.get(User, user_id)
        if not user:
            raise NotFoundException("User profile not found.")
        return user

    @staticmethod
    def update_user_profile(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update current user profile information."""
        user = UserService.get_user_by_id(user_id)

        if "email" in data and data["email"]:
            new_email = data["email"].strip().lower()
            if new_email != user.email:
                existing = User.query.filter_by(email=new_email).first()
                if existing:
                    raise ConflictException("An account with this email already exists.")
                user.email = new_email

        if "name" in data and data["name"]:
            user.name = data["name"].strip()

        db.session.commit()
        return user.to_dict()

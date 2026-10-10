"""Authentication service for handling registration, login, and token management."""
from typing import Dict, Any, Tuple
from flask_jwt_extended import create_access_token, create_refresh_token
from app.extensions import db
from app.models.user import User
from app.models.token_blocklist import TokenBlocklist
from app.utils.error_handlers import (
    ConflictException,
    UnauthorizedException,
    NotFoundException,
)


class AuthService:
    """Service encapsulating authentication logic."""

    @staticmethod
    def register_user(data: Dict[str, Any]) -> Tuple[Dict[str, Any], User]:
        """Register a new user and generate initial tokens."""
        email = data["email"].strip().lower()
        existing = User.query.filter_by(email=email).first()
        if existing:
            raise ConflictException("An account with this email address already exists.")

        # Public registration always creates pet_owner accounts
        user = User(
            name=data["name"].strip(),
            email=email,
            password=data["password"],
            role=User.ROLE_PET_OWNER,
        )
        db.session.add(user)
        db.session.commit()

        # Generate tokens with role claims
        access_token = create_access_token(
            identity=user.id,
            additional_claims={"role": user.role},
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            additional_claims={"role": user.role},
        )

        response_data = {
            "user": user.to_dict(),
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
            },
        }
        return response_data, user

    @staticmethod
    def login_user(data: Dict[str, Any]) -> Tuple[Dict[str, Any], User]:
        """Authenticate user credentials and issue tokens."""
        email = data["email"].strip().lower()
        password = data["password"]

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            raise UnauthorizedException("Invalid email or password.")

        access_token = create_access_token(
            identity=user.id,
            additional_claims={"role": user.role},
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            additional_claims={"role": user.role},
        )

        response_data = {
            "user": user.to_dict(),
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
            },
        }
        return response_data, user

    @staticmethod
    def refresh_access_token(user_id: str) -> Dict[str, str]:
        """Issue a new access token for a valid refresh token."""
        user = db.session.get(User, user_id)
        if not user:
            raise NotFoundException("User associated with this token not found.")

        new_access_token = create_access_token(
            identity=user.id,
            additional_claims={"role": user.role},
        )
        return {
            "access_token": new_access_token,
            "token_type": "Bearer",
        }

    @staticmethod
    def logout_token(jti: str, token_type: str) -> None:
        """Revoke a token by saving its JTI to the blocklist."""
        revoked_token = TokenBlocklist(jti=jti, token_type=token_type)
        db.session.add(revoked_token)
        db.session.commit()

    @staticmethod
    def get_user_profile(user_id: str) -> Dict[str, Any]:
        """Fetch current user's profile."""
        user = db.session.get(User, user_id)
        if not user:
            raise NotFoundException("User not found.")
        return user.to_dict()

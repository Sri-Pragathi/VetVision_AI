"""Security utilities for password hashing and verification."""
import bcrypt


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with a generated salt."""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def check_password(password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    if not password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def doctor_required():
    """Route decorator enforcing authenticated Doctor role from JWT claims."""
    from functools import wraps
    from flask_jwt_extended import get_jwt, get_jwt_identity
    from app.utils.error_handlers import ForbiddenException
    from app.extensions import db
    from app.models.user import User

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            claims = get_jwt()
            role = claims.get("role")
            if not role:
                user_id = get_jwt_identity()
                user = db.session.get(User, user_id)
                role = user.role if user else None
            if role != User.ROLE_DOCTOR:
                raise ForbiddenException("Doctor access required for this endpoint.")
            return fn(*args, **kwargs)
        return decorator
    return wrapper


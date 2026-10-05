"""Validation utility functions and custom validators."""
import re
import uuid
from datetime import date
from marshmallow import ValidationError

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

ALLOWED_SEX_CHOICES = {
    "male",
    "female",
    "male neutered",
    "female spayed",
    "neutered",
    "spayed",
    "unknown",
}


def validate_email_format(email: str) -> None:
    """Validate email format."""
    if not email or not isinstance(email, str):
        raise ValidationError("Email address is required.")
    cleaned = email.strip()
    if len(cleaned) > 255:
        raise ValidationError("Email address must not exceed 255 characters.")
    if not EMAIL_REGEX.match(cleaned):
        raise ValidationError("Invalid email address format.")


def validate_password_strength(password: str) -> None:
    """Validate password strength (at least 8 chars, containing letter and number)."""
    if not password or not isinstance(password, str):
        raise ValidationError("Password is required.")
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if len(password) > 128:
        raise ValidationError("Password cannot exceed 128 characters.")
    if not re.search(r"[A-Za-z]", password):
        raise ValidationError("Password must contain at least one letter.")
    if not re.search(r"[0-9]", password):
        raise ValidationError("Password must contain at least one digit.")


def validate_name(name: str) -> None:
    """Validate person or pet name."""
    if not name or not isinstance(name, str):
        raise ValidationError("Name is required.")
    cleaned = name.strip()
    if len(cleaned) < 2:
        raise ValidationError("Name must be at least 2 characters long.")
    if len(cleaned) > 100:
        raise ValidationError("Name cannot exceed 100 characters.")


def validate_species(species: str) -> None:
    """Validate pet species."""
    if not species or not isinstance(species, str):
        raise ValidationError("Species is required.")
    cleaned = species.strip()
    if len(cleaned) < 2:
        raise ValidationError("Species must be at least 2 characters long.")
    if len(cleaned) > 50:
        raise ValidationError("Species cannot exceed 50 characters.")


def validate_sex(sex: str) -> None:
    """Validate pet sex if provided."""
    if sex is None:
        return
    cleaned = sex.strip().lower()
    if cleaned not in ALLOWED_SEX_CHOICES:
        raise ValidationError(
            f"Invalid sex value. Allowed choices: {', '.join(sorted(ALLOWED_SEX_CHOICES))}"
        )


def validate_weight(weight: float) -> None:
    """Validate pet weight if provided."""
    if weight is None:
        return
    if weight <= 0:
        raise ValidationError("Weight must be greater than 0.")
    if weight > 1000:
        raise ValidationError("Weight value is unrealistic (max 1000 kg/lbs).")


def validate_past_date(d: date) -> None:
    """Validate that date is not in the future."""
    if d and d > date.today():
        raise ValidationError("Date cannot be in the future.")


def is_valid_uuid(val: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid_obj = uuid.UUID(str(val))
        return str(uuid_obj) == str(val)
    except (ValueError, AttributeError, TypeError):
        return False

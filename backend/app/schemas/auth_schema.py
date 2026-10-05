"""Marshmallow validation schemas for authentication."""
from marshmallow import Schema, fields
from app.utils.validators import (
    validate_email_format,
    validate_password_strength,
    validate_name,
)


class RegisterSchema(Schema):
    """Schema for user registration payload."""
    name = fields.String(
        required=True,
        validate=validate_name,
        error_messages={"required": "Name is required."},
    )
    email = fields.String(
        required=True,
        validate=validate_email_format,
        error_messages={"required": "Email is required."},
    )
    password = fields.String(
        required=True,
        validate=validate_password_strength,
        load_only=True,
        error_messages={"required": "Password is required."},
    )


class LoginSchema(Schema):
    """Schema for user login credentials."""
    email = fields.String(
        required=True,
        validate=validate_email_format,
        error_messages={"required": "Email is required."},
    )
    password = fields.String(
        required=True,
        load_only=True,
        error_messages={"required": "Password is required."},
    )


register_schema = RegisterSchema()
login_schema = LoginSchema()

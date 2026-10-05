"""Marshmallow schemas for user profile management."""
from marshmallow import Schema, fields
from app.utils.validators import validate_email_format, validate_name


class UserProfileSchema(Schema):
    """Schema for serializing user profile information."""
    id = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    email = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class UserUpdateSchema(Schema):
    """Schema for updating user profile information."""
    name = fields.String(
        required=False,
        validate=validate_name,
    )
    email = fields.String(
        required=False,
        validate=validate_email_format,
    )


user_profile_schema = UserProfileSchema()
user_update_schema = UserUpdateSchema()

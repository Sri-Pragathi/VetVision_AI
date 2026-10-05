"""Marshmallow validation and serialization schemas for Pet entities."""
from marshmallow import Schema, fields, validate
from app.utils.validators import (
    validate_name,
    validate_species,
    validate_sex,
    validate_weight,
    validate_past_date,
)


class PetCreateSchema(Schema):
    """Schema for registering a new pet."""
    name = fields.String(
        required=True,
        validate=validate_name,
        error_messages={"required": "Pet name is required."},
    )
    species = fields.String(
        required=True,
        validate=validate_species,
        error_messages={"required": "Pet species is required."},
    )
    breed = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    sex = fields.String(
        required=False,
        allow_none=True,
        validate=validate_sex,
    )
    date_of_birth = fields.Date(
        required=False,
        allow_none=True,
        validate=validate_past_date,
    )
    weight = fields.Float(
        required=False,
        allow_none=True,
        validate=validate_weight,
    )
    allergies = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000),
    )
    existing_conditions = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000),
    )
    current_medications = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000),
    )
    vaccination_status = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
    )


class PetUpdateSchema(Schema):
    """Schema for updating an existing pet profile."""
    name = fields.String(
        required=False,
        validate=validate_name,
    )
    species = fields.String(
        required=False,
        validate=validate_species,
    )
    breed = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    sex = fields.String(
        required=False,
        allow_none=True,
        validate=validate_sex,
    )
    date_of_birth = fields.Date(
        required=False,
        allow_none=True,
        validate=validate_past_date,
    )
    weight = fields.Float(
        required=False,
        allow_none=True,
        validate=validate_weight,
    )
    allergies = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000),
    )
    existing_conditions = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000),
    )
    current_medications = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000),
    )
    vaccination_status = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
    )


class PetResponseSchema(Schema):
    """Schema for serializing pet entity responses."""
    id = fields.String(dump_only=True)
    owner_id = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    species = fields.String(dump_only=True)
    breed = fields.String(dump_only=True)
    sex = fields.String(dump_only=True)
    date_of_birth = fields.Date(dump_only=True)
    age = fields.Integer(dump_only=True)
    weight = fields.Float(dump_only=True)
    allergies = fields.String(dump_only=True)
    existing_conditions = fields.String(dump_only=True)
    current_medications = fields.String(dump_only=True)
    vaccination_status = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


pet_create_schema = PetCreateSchema()
pet_update_schema = PetUpdateSchema()
pet_response_schema = PetResponseSchema()
pets_response_schema = PetResponseSchema(many=True)

"""Schemas for doctor review validation and serialization."""
from marshmallow import Schema, fields, validate


class DoctorReviewCreateSchema(Schema):
    """Schema for creating a doctor clinical review."""
    assessment_id = fields.String(required=False, allow_none=True)
    status = fields.String(
        validate=validate.OneOf(["pending", "reviewed"]),
        load_default="reviewed",
    )
    override_triage_level = fields.String(
        validate=validate.OneOf(["non_urgent", "routine", "urgent", "critical"]),
        allow_none=True,
    )
    doctor_notes = fields.String(allow_none=True)
    recommendations = fields.String(allow_none=True)
    prescriptions = fields.String(allow_none=True)


class DoctorReviewResponseSchema(Schema):
    """Schema for serializing a doctor review."""
    id = fields.String(dump_only=True)
    assessment_id = fields.String(dump_only=True)
    doctor_id = fields.String(dump_only=True)
    doctor_name = fields.String(dump_only=True, allow_none=True)
    status = fields.String(dump_only=True)
    override_triage_level = fields.String(dump_only=True, allow_none=True)
    doctor_notes = fields.String(dump_only=True, allow_none=True)
    recommendations = fields.String(dump_only=True, allow_none=True)
    prescriptions = fields.String(dump_only=True, allow_none=True)
    reviewed_at = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

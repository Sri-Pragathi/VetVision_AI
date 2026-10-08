"""Marshmallow schemas for serializing pet images and visual observations."""
from marshmallow import Schema, fields


class ImageObservationResponseSchema(Schema):
    """Schema for serializing a single computer-vision observation."""
    id = fields.String(dump_only=True)
    assessment_image_id = fields.String(dump_only=True)
    observation_type = fields.String(dump_only=True)
    observation_label = fields.String(dump_only=True)
    severity = fields.String(dump_only=True)
    region = fields.String(dump_only=True)
    description = fields.String(dump_only=True)
    source = fields.String(dump_only=True)
    model_version = fields.String(dump_only=True)
    extra_data = fields.Dict(dump_only=True)
    created_at = fields.String(dump_only=True)


class AssessmentImageResponseSchema(Schema):
    """Schema for serializing an assessment image record."""
    id = fields.String(dump_only=True)
    assessment_id = fields.String(dump_only=True)
    pet_id = fields.String(dump_only=True)
    original_filename = fields.String(dump_only=True)
    mime_type = fields.String(dump_only=True)
    file_size = fields.Integer(dump_only=True)
    width = fields.Integer(dump_only=True)
    height = fields.Integer(dump_only=True)
    processing_status = fields.String(dump_only=True)
    analysis_status = fields.String(dump_only=True)
    quality_gate = fields.String(dump_only=True)
    observations = fields.List(fields.Nested(ImageObservationResponseSchema), dump_only=True)
    created_at = fields.String(dump_only=True)
    updated_at = fields.String(dump_only=True)


image_observation_response_schema = ImageObservationResponseSchema()
image_observations_response_schema = ImageObservationResponseSchema(many=True)
assessment_image_response_schema = AssessmentImageResponseSchema()
assessment_images_response_schema = AssessmentImageResponseSchema(many=True)

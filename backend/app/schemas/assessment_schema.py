"""Marshmallow validation and serialization schemas for health assessments."""
from marshmallow import Schema, fields, validate, validates, ValidationError
from app.models.assessment_symptom import AssessmentSymptom
from app.models.health_observation import HealthObservation
from app.models.health_assessment import HealthAssessment
from app.utils.validators import is_valid_uuid


class SymptomResponseSchema(Schema):
    """Schema for serializing symptoms."""
    id = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    category = fields.String(dump_only=True)
    description = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class AssessmentSymptomCreateSchema(Schema):
    """Schema for attaching a symptom to an assessment."""
    symptom_id = fields.String(
        required=True,
        error_messages={"required": "Symptom ID is required."},
    )
    severity = fields.String(
        required=True,
        validate=validate.OneOf(
            AssessmentSymptom.VALID_SEVERITIES,
            error="Severity must be one of: mild, moderate, severe.",
        ),
        error_messages={"required": "Severity is required."},
    )
    duration_value = fields.Float(
        required=True,
        validate=validate.Range(min=0.1, max=3650.0, min_inclusive=True, error="Duration value must be positive."),
        error_messages={"required": "Duration value is required."},
    )
    duration_unit = fields.String(
        required=True,
        validate=validate.OneOf(
            AssessmentSymptom.VALID_DURATION_UNITS,
            error="Duration unit must be one of: hours, days, weeks, months.",
        ),
        error_messages={"required": "Duration unit is required."},
    )
    notes = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000, error="Notes cannot exceed 1000 characters."),
    )

    @validates("symptom_id")
    def validate_symptom_uuid(self, value):
        if not is_valid_uuid(value):
            raise ValidationError("Invalid symptom UUID format.")


class AssessmentSymptomUpdateSchema(Schema):
    """Schema for updating an attached symptom."""
    severity = fields.String(
        required=False,
        validate=validate.OneOf(
            AssessmentSymptom.VALID_SEVERITIES,
            error="Severity must be one of: mild, moderate, severe.",
        ),
    )
    duration_value = fields.Float(
        required=False,
        validate=validate.Range(min=0.1, max=3650.0, min_inclusive=True, error="Duration value must be positive."),
    )
    duration_unit = fields.String(
        required=False,
        validate=validate.OneOf(
            AssessmentSymptom.VALID_DURATION_UNITS,
            error="Duration unit must be one of: hours, days, weeks, months.",
        ),
    )
    notes = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000, error="Notes cannot exceed 1000 characters."),
    )


class HealthObservationSchema(Schema):
    """Schema for structured clinical observations."""
    appetite = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(
            HealthObservation.APPETITE_CHOICES,
            error="Invalid appetite value. Options: " + ", ".join(sorted(HealthObservation.APPETITE_CHOICES)),
        ),
    )
    water_intake = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(
            HealthObservation.WATER_INTAKE_CHOICES,
            error="Invalid water_intake value. Options: " + ", ".join(sorted(HealthObservation.WATER_INTAKE_CHOICES)),
        ),
    )
    activity_level = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(
            HealthObservation.ACTIVITY_LEVEL_CHOICES,
            error="Invalid activity_level value. Options: " + ", ".join(sorted(HealthObservation.ACTIVITY_LEVEL_CHOICES)),
        ),
    )
    behaviour_change = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(
            HealthObservation.BEHAVIOUR_CHANGE_CHOICES,
            error="Invalid behaviour_change value. Options: " + ", ".join(sorted(HealthObservation.BEHAVIOUR_CHANGE_CHOICES)),
        ),
    )
    sleep_change = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(
            HealthObservation.SLEEP_CHANGE_CHOICES,
            error="Invalid sleep_change value. Options: " + ", ".join(sorted(HealthObservation.SLEEP_CHANGE_CHOICES)),
        ),
    )
    stool_change = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(
            HealthObservation.STOOL_CHANGE_CHOICES,
            error="Invalid stool_change value. Options: " + ", ".join(sorted(HealthObservation.STOOL_CHANGE_CHOICES)),
        ),
    )
    urine_change = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(
            HealthObservation.URINE_CHANGE_CHOICES,
            error="Invalid urine_change value. Options: " + ", ".join(sorted(HealthObservation.URINE_CHANGE_CHOICES)),
        ),
    )
    breathing_change = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(
            HealthObservation.BREATHING_CHANGE_CHOICES,
            error="Invalid breathing_change value. Options: " + ", ".join(sorted(HealthObservation.BREATHING_CHANGE_CHOICES)),
        ),
    )
    pain_observed = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(
            HealthObservation.PAIN_OBSERVED_CHOICES,
            error="Invalid pain_observed value. Options: " + ", ".join(sorted(HealthObservation.PAIN_OBSERVED_CHOICES)),
        ),
    )


class AssessmentNoteCreateSchema(Schema):
    """Schema for adding an assessment free-text note."""
    note = fields.String(
        required=True,
        validate=[
            validate.Length(min=1, error="Note cannot be empty."),
            validate.Length(max=5000, error="Note cannot exceed 5000 characters."),
        ],
        error_messages={"required": "Note text is required."},
    )


class AssessmentStatusUpdateSchema(Schema):
    """Schema for updating assessment lifecycle status."""
    status = fields.String(
        required=True,
        validate=validate.OneOf(
            HealthAssessment.VALID_STATUSES,
            error="Status must be one of: in_progress, completed, cancelled.",
        ),
        error_messages={"required": "Status is required."},
    )


class AssessmentDurationNestedSchema(Schema):
    value = fields.Float()
    unit = fields.String()


class AssessmentSymptomResponseSchema(Schema):
    id = fields.String()
    assessment_id = fields.String()
    symptom_id = fields.String()
    symptom_name = fields.String()
    symptom_category = fields.String()
    severity = fields.String()
    duration_value = fields.Float()
    duration_unit = fields.String()
    duration = fields.Nested(AssessmentDurationNestedSchema)
    notes = fields.String()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class AssessmentNoteResponseSchema(Schema):
    id = fields.String()
    assessment_id = fields.String()
    note = fields.String()
    created_at = fields.DateTime()


class HealthAssessmentResponseSchema(Schema):
    id = fields.String()
    pet_id = fields.String()
    status = fields.String()
    started_at = fields.DateTime()
    completed_at = fields.DateTime()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    symptoms = fields.List(fields.Nested(AssessmentSymptomResponseSchema))
    observations = fields.Nested(HealthObservationSchema, allow_none=True)
    notes = fields.List(fields.Nested(AssessmentNoteResponseSchema))


symptom_response_schema = SymptomResponseSchema()
symptoms_response_schema = SymptomResponseSchema(many=True)
assessment_symptom_create_schema = AssessmentSymptomCreateSchema()
assessment_symptom_update_schema = AssessmentSymptomUpdateSchema()
health_observation_schema = HealthObservationSchema()
assessment_note_create_schema = AssessmentNoteCreateSchema()
assessment_status_update_schema = AssessmentStatusUpdateSchema()
health_assessment_response_schema = HealthAssessmentResponseSchema()
health_assessments_response_schema = HealthAssessmentResponseSchema(many=True)

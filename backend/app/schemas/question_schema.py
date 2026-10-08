"""Marshmallow validation and serialization schemas for dynamic follow-up questions and answers."""
from marshmallow import Schema, fields, validate, validates, validates_schema, ValidationError
from app.models.follow_up_question import FollowUpQuestion
from app.utils.validators import is_valid_uuid


# ---------------------------------------------------------------------------
# Question Schemas
# ---------------------------------------------------------------------------

class QuestionOptionResponseSchema(Schema):
    """Schema for serializing a question option."""
    id = fields.String(dump_only=True)
    question_id = fields.String(dump_only=True)
    option_text = fields.String(dump_only=True)
    option_value = fields.String(dump_only=True)
    severity_weight = fields.Float(dump_only=True, allow_none=True)
    emergency_flag = fields.Boolean(dump_only=True)
    display_order = fields.Integer(dump_only=True)


class FollowUpQuestionResponseSchema(Schema):
    """Schema for serializing a follow-up question with its options."""
    id = fields.String(dump_only=True)
    question_text = fields.String(dump_only=True)
    question_type = fields.String(dump_only=True)
    category = fields.String(dump_only=True, allow_none=True)
    priority = fields.String(dump_only=True)
    symptom_id = fields.String(dump_only=True, allow_none=True)
    species = fields.String(dump_only=True, allow_none=True)
    min_age_months = fields.Integer(dump_only=True, allow_none=True)
    max_age_months = fields.Integer(dump_only=True, allow_none=True)
    is_emergency_related = fields.Boolean(dump_only=True)
    is_active = fields.Boolean(dump_only=True)
    display_order = fields.Integer(dump_only=True)
    options = fields.List(fields.Nested(QuestionOptionResponseSchema), dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class QuestionFilterSchema(Schema):
    """Schema for validating query parameters on GET /questions."""
    symptom_id = fields.String(
        required=False,
        load_default=None,
    )
    category = fields.String(
        required=False,
        load_default=None,
    )
    species = fields.String(
        required=False,
        load_default=None,
    )
    priority = fields.String(
        required=False,
        load_default=None,
        validate=validate.OneOf(
            FollowUpQuestion.VALID_PRIORITIES,
            error="Priority must be one of: emergency, high, medium, low.",
        ),
    )

    @validates("symptom_id")
    def validate_symptom_uuid(self, value):
        if value and not is_valid_uuid(value):
            raise ValidationError("Invalid symptom UUID format.")


# ---------------------------------------------------------------------------
# Answer Schemas
# ---------------------------------------------------------------------------

class AnswerSubmitSchema(Schema):
    """Schema for validating answer submission to a follow-up question."""
    question_id = fields.String(
        required=True,
        error_messages={"required": "question_id is required."},
    )
    selected_option_id = fields.String(
        required=False,
        allow_none=True,
        load_default=None,
    )
    answer_text = fields.String(
        required=False,
        allow_none=True,
        load_default=None,
        validate=validate.Length(max=2000, error="answer_text cannot exceed 2000 characters."),
    )
    numeric_value = fields.Float(
        required=False,
        allow_none=True,
        load_default=None,
        validate=validate.Range(
            min=0, max=999999,
            error="numeric_value must be a non-negative number.",
        ),
    )
    boolean_value = fields.Boolean(
        required=False,
        allow_none=True,
        load_default=None,
    )

    @validates("question_id")
    def validate_question_uuid(self, value):
        if not is_valid_uuid(value):
            raise ValidationError("Invalid question_id UUID format.")

    @validates("selected_option_id")
    def validate_option_uuid(self, value):
        if value and not is_valid_uuid(value):
            raise ValidationError("Invalid selected_option_id UUID format.")

    @validates_schema
    def validate_at_least_one_value(self, data, **kwargs):
        """Ensure at least one answer value is provided."""
        has_value = (
            data.get("selected_option_id") is not None
            or data.get("answer_text") is not None
            or data.get("numeric_value") is not None
            or data.get("boolean_value") is not None
        )
        if not has_value:
            raise ValidationError(
                "At least one answer value must be provided: "
                "selected_option_id, answer_text, numeric_value, or boolean_value.",
                field_name="_schema",
            )


class AnswerResponseSchema(Schema):
    """Schema for serializing a submitted assessment answer."""
    id = fields.String(dump_only=True)
    assessment_id = fields.String(dump_only=True)
    question_id = fields.String(dump_only=True)
    selected_option_id = fields.String(dump_only=True, allow_none=True)
    answer_text = fields.String(dump_only=True, allow_none=True)
    numeric_value = fields.Float(dump_only=True, allow_none=True)
    boolean_value = fields.Boolean(dump_only=True, allow_none=True)
    triggered_emergency = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    selected_option = fields.Nested(QuestionOptionResponseSchema, dump_only=True, allow_none=True)
    question = fields.Nested(FollowUpQuestionResponseSchema, dump_only=True, allow_none=True)


# Shared instances
question_response_schema = FollowUpQuestionResponseSchema()
questions_response_schema = FollowUpQuestionResponseSchema(many=True)
question_filter_schema = QuestionFilterSchema()
answer_submit_schema = AnswerSubmitSchema()
answer_response_schema = AnswerResponseSchema()
answers_response_schema = AnswerResponseSchema(many=True)

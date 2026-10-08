"""Risk Analysis schemas for serializing and validating risk analysis output."""
from marshmallow import Schema, fields


class RiskAnalysisResponseSchema(Schema):
    """Schema for serializing AssessmentRiskAnalysis entity."""
    id = fields.String(dump_only=True)
    assessment_id = fields.String(dump_only=True)
    risk_level = fields.String(dump_only=True)
    risk_score = fields.Integer(dump_only=True)
    key_factors = fields.List(fields.String(), dump_only=True)
    factor_breakdown = fields.Dict(dump_only=True)
    recommendation = fields.String(dump_only=True)
    emergency = fields.Boolean(dump_only=True)
    is_emergency = fields.Boolean(dump_only=True)
    engine_version = fields.String(dump_only=True)
    disclaimer = fields.String(dump_only=True)
    created_at = fields.String(dump_only=True)
    updated_at = fields.String(dump_only=True)


risk_analysis_response_schema = RiskAnalysisResponseSchema()

"""Assessment Report schemas for serialization."""
from marshmallow import Schema, fields


class AssessmentReportResponseSchema(Schema):
    """Schema for serializing AssessmentReport entity."""
    id = fields.String(dump_only=True)
    assessment_id = fields.String(dump_only=True)
    report_version = fields.Integer(dump_only=True)
    report_status = fields.String(dump_only=True)
    generated_at = fields.DateTime(dump_only=True)
    generated_by = fields.String(dump_only=True)
    report_data = fields.Dict(dump_only=True)
    disclaimer = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class AssessmentReportSummarySchema(Schema):
    """Schema for listing AssessmentReport summaries without full payload."""
    id = fields.String(dump_only=True)
    assessment_id = fields.String(dump_only=True)
    report_version = fields.Integer(dump_only=True)
    report_status = fields.String(dump_only=True)
    generated_at = fields.DateTime(dump_only=True)
    generated_by = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


assessment_report_response_schema = AssessmentReportResponseSchema()
assessment_reports_response_schema = AssessmentReportResponseSchema(many=True)
assessment_report_summary_schema = AssessmentReportSummarySchema()
assessment_reports_summary_schema = AssessmentReportSummarySchema(many=True)

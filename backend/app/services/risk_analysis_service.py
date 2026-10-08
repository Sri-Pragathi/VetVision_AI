"""Risk Analysis Service coordinating data intake, engine execution, and persistence."""
from typing import Dict, Any, Optional
from app.extensions import db
from app.models.health_assessment import HealthAssessment
from app.models.risk_analysis import AssessmentRiskAnalysis
from app.services.ai_data_service import AiDataPreparationService
from app.services.assessment_service import AssessmentService
from app.services.risk_engine.base import BaseRiskAnalysisEngine
from app.services.risk_engine.rule_engine import RuleBasedRiskAnalysisEngine
from app.utils.error_handlers import (
    NotFoundException,
    ValidationException,
)


class RiskAnalysisService:
    """Coordinates AI health risk analysis for clinical assessments.

    Architecturally decouples the scoring engine from storage and routing,
    supporting pluggable AI engines (rule-based heuristic or ML models).
    """

    _default_engine: BaseRiskAnalysisEngine = RuleBasedRiskAnalysisEngine()

    @classmethod
    def set_default_engine(cls, engine: BaseRiskAnalysisEngine) -> None:
        """Allow runtime registration of alternative risk analysis engines (e.g. ML models)."""
        cls._default_engine = engine

    @classmethod
    def get_default_engine(cls) -> BaseRiskAnalysisEngine:
        """Return the active risk analysis engine."""
        return cls._default_engine

    @classmethod
    def analyze_assessment(
        cls,
        assessment_id: str,
        user_id: str,
        engine: Optional[BaseRiskAnalysisEngine] = None,
    ) -> Dict[str, Any]:
        """Perform explainable health risk analysis on an assessment and store result.

        Args:
            assessment_id: UUID of the assessment session.
            user_id: Authenticated user UUID for ownership verification.
            engine: Optional custom risk analysis engine. Defaults to RuleBasedRiskAnalysisEngine.

        Returns:
            Dictionary containing stored risk analysis results with factors,
            scores, recommendations, and disclaimers.

        Raises:
            NotFoundException: If assessment does not exist.
            ForbiddenException: If assessment belongs to another user.
            ValidationException: If assessment is cancelled or has no symptoms.
        """
        # 1. Enforce ownership and existence
        assessment = AssessmentService._verify_assessment_ownership(assessment_id, user_id)

        # 2. Validate assessment state
        if assessment.status == HealthAssessment.STATUS_CANCELLED:
            raise ValidationException("Cannot perform risk analysis on a cancelled assessment.")

        if not assessment.symptoms:
            raise ValidationException(
                "Assessment must have at least one reported symptom to evaluate health risk."
            )

        # 3. Prepare complete AI payload (Steps 1–3 data)
        payload = AiDataPreparationService.prepare_ai_payload(assessment)

        # 4. Execute Risk Analysis Engine
        active_engine = engine or cls._default_engine
        output = active_engine.analyze(payload)

        # 5. Persist or Upsert Result (Avoid duplicate records)
        analysis = AssessmentRiskAnalysis.query.filter_by(assessment_id=assessment.id).first()
        if not analysis:
            analysis = AssessmentRiskAnalysis(assessment_id=assessment.id)
            db.session.add(analysis)

        analysis.risk_level = output.risk_level
        analysis.risk_score = output.risk_score
        analysis.key_factors = output.key_factors
        analysis.factor_breakdown = output.factor_breakdown
        analysis.recommendation = output.recommendation
        analysis.is_emergency = output.is_emergency
        analysis.engine_version = output.engine_version
        analysis.disclaimer = output.disclaimer

        db.session.commit()

        return analysis.to_dict()

    @classmethod
    def get_assessment_risk_analysis(
        cls, assessment_id: str, user_id: str
    ) -> Dict[str, Any]:
        """Retrieve the latest stored risk analysis for an assessment.

        Args:
            assessment_id: UUID of the assessment.
            user_id: Authenticated user UUID for ownership verification.

        Returns:
            Dictionary of stored risk analysis.

        Raises:
            NotFoundException: If assessment or risk analysis not found.
            ForbiddenException: If assessment belongs to another user.
        """
        # Enforce ownership
        assessment = AssessmentService._verify_assessment_ownership(assessment_id, user_id)

        analysis = AssessmentRiskAnalysis.query.filter_by(assessment_id=assessment.id).first()
        if not analysis:
            raise NotFoundException(
                f"No risk analysis has been generated for assessment '{assessment_id}' yet."
            )

        return analysis.to_dict()

"""Abstract base class and contract for health risk analysis engines.

This defines the clean interface allowing seamless replacement or augmentation
with trained machine learning models (e.g., PyTorch, ONNX, scikit-learn)
without requiring changes to the service, routing, or data persistence layers.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class RiskAnalysisOutput:
    """Standardized output structure for risk analysis results."""
    risk_level: str  # LOW, MODERATE, HIGH, EMERGENCY
    risk_score: int  # 0 to 100
    key_factors: List[str] = field(default_factory=list)
    factor_breakdown: Dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""
    is_emergency: bool = False
    structured_factors: List[Dict[str, Any]] = field(default_factory=list)
    data_quality_warnings: List[Dict[str, Any]] = field(default_factory=list)
    engine_version: str = "v1.1.0-rule_explainable"
    disclaimer: str = (
        "This assessment is for early-warning support and does not replace "
        "professional veterinary diagnosis. If your pet is in acute distress, "
        "contact an emergency veterinary hospital immediately."
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert output to standard dictionary."""
        return {
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "key_factors": self.key_factors,
            "factor_breakdown": self.factor_breakdown,
            "structured_factors": self.structured_factors,
            "data_quality_warnings": self.data_quality_warnings,
            "recommendation": self.recommendation,
            "emergency": self.is_emergency,
            "is_emergency": self.is_emergency,
            "engine_version": self.engine_version,
            "disclaimer": self.disclaimer,
        }


class BaseRiskAnalysisEngine(ABC):
    """Abstract interface for all health risk analysis implementations."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Return the engine version string."""
        pass

    @abstractmethod
    def analyze(self, payload: Dict[str, Any]) -> RiskAnalysisOutput:
        """Analyze structured assessment payload and return explainable risk metrics.

        Args:
            payload: AI-ready dictionary prepared by AiDataPreparationService,
                     containing pet baseline, symptoms, observations, notes,
                     and follow-up answers.

        Returns:
            RiskAnalysisOutput with standardized risk score, level, factors,
            and recommendations.
        """
        pass

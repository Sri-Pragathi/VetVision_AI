"""Abstract base class and contract for computer vision / image analysis engines.

Provides a clean interface allowing future integration of real, validated
veterinary computer-vision models (e.g. YOLO, PyTorch, ONNX) without altering
routes, database schemas, or assessment services.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class ImageAnalysisOutput:
    """Standardized output structure for computer-vision results."""
    status: str  # SUCCESS, REQUIRES_BETTER_IMAGE, FAILED
    quality_gate: str  # PASSED, REQUIRES_BETTER_IMAGE
    quality_score: float  # 0.0 to 1.0
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    visual_observations: List[Dict[str, Any]] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    recommendation: str = ""
    engine_version: str = "v1.0.0-cv_baseline"
    disclaimer: str = (
        "This image analysis provides computational computer-vision observations "
        "for early-warning support and does not replace professional veterinary "
        "examination or diagnosis."
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert output to standard dictionary."""
        return {
            "status": self.status,
            "quality_gate": self.quality_gate,
            "quality_score": round(self.quality_score, 2),
            "quality_metrics": self.quality_metrics,
            "visual_observations": self.visual_observations,
            "reasons": self.reasons,
            "recommendation": self.recommendation,
            "engine_version": self.engine_version,
            "disclaimer": self.disclaimer,
        }


class BaseImageAnalysisEngine(ABC):
    """Abstract interface for all computer vision engines."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Return the computer vision engine version string."""
        pass

    @abstractmethod
    def analyze_image(
        self, image_path: str, context: Optional[Dict[str, Any]] = None
    ) -> ImageAnalysisOutput:
        """Run computer vision processing on an image file.

        Args:
            image_path: Absolute local path to image file.
            context: Optional clinical context (symptoms, pet species, observations).

        Returns:
            ImageAnalysisOutput containing quality metrics, observations, and recommendations.
        """
        pass

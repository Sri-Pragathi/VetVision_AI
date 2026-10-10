"""Structured explainability factor model for VetVision AI Risk Engine.

Provides transparent attribution of clinical findings:
- Source of evidence
- Status (PRESENT, ABSENT, UNKNOWN, CONTRADICTORY)
- Directional impact (risk_increasing, reassuring, unknown, emergency_override)
- Explicit rule applied and clinical rationale
- Exact numerical contribution points when calculated by the scoring formula
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class StructuredFactor:
    """Detailed explainable risk factor attributing finding to scoring rule."""
    factor_name: str
    finding: str
    source: str
    status: str
    direction: str
    rule_applied: str
    rationale: str
    contribution_pts: Optional[int] = None
    is_emergency_flag: bool = False
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert structured factor to clean dictionary."""
        return {
            "factor_name": self.factor_name,
            "finding": self.finding,
            "source": self.source,
            "status": self.status,
            "direction": self.direction,
            "rule_applied": self.rule_applied,
            "rationale": self.rationale,
            "contribution_pts": self.contribution_pts,
            "is_emergency_flag": self.is_emergency_flag,
            "details": self.details,
        }

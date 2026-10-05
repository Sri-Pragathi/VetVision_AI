"""Emergency detection service interface providing preliminary triage classification."""
from typing import Dict, Any, List, Optional
from app.models.health_assessment import HealthAssessment
from app.services.ai_data_service import AiDataPreparationService


class EmergencyAssessmentService:
    """Architectural interface for emergency triage detection and prioritization.
    
    NOTE: This is a placeholder architectural interface for future machine learning
    and rule-based triage integration. It provides preliminary flag evaluation
    and safety disclaimers, without making final veterinary medical claims.
    """

    CRITICAL_SYMPTOM_NAMES = {
        "difficulty breathing",
        "seizures",
        "collapse",
        "severe bleeding",
        "unresponsiveness",
    }

    @classmethod
    def evaluate_emergency_risk(
        cls, assessment: HealthAssessment
    ) -> Dict[str, Any]:
        """Evaluate an assessment for acute clinical emergency flags."""
        ai_data = AiDataPreparationService.prepare_ai_payload(assessment)
        return cls.evaluate_payload(ai_data)

    @classmethod
    def evaluate_payload(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate structured assessment data for potential acute warning signs."""
        flags: List[str] = []
        is_emergency = False
        risk_level = "routine"

        # Check symptoms for critical indicators
        symptoms = data.get("symptoms", [])
        for sym in symptoms:
            name = (sym.get("name") or "").lower()
            severity = (sym.get("severity") or "").lower()

            if name in cls.CRITICAL_SYMPTOM_NAMES and severity in ("moderate", "severe"):
                flags.append(f"Acute indicator: {name} ({severity})")
                is_emergency = True
                risk_level = "emergency"
            elif severity == "severe":
                flags.append(f"Severe symptom observed: {name}")
                if risk_level != "emergency":
                    risk_level = "urgent"

        # Check observations for labored breathing or severe pain
        obs = data.get("observations", {})
        if obs.get("breathing_change") in ("labored", "wheezing"):
            flags.append(f"Abnormal respiration: {obs.get('breathing_change')}")
            is_emergency = True
            risk_level = "emergency"

        if obs.get("pain_observed") == "severe":
            flags.append("Severe pain reported")
            if risk_level != "emergency":
                risk_level = "urgent"

        recommendation = (
            "Immediate emergency veterinary consultation recommended."
            if is_emergency
            else (
                "Prompt veterinary examination recommended within 24 hours."
                if risk_level == "urgent"
                else "Routine veterinary monitoring recommended."
            )
        )

        return {
            "is_emergency_flagged": is_emergency,
            "risk_level": risk_level,
            "flags": flags,
            "recommendation": recommendation,
            "disclaimer": (
                "VetVision AI triage screening is an assistive computational tool "
                "and does not constitute a veterinary medical diagnosis. If your pet "
                "is in acute distress, seek emergency veterinary attention immediately."
            ),
        }

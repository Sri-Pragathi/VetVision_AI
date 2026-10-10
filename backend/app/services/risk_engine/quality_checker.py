"""Data quality, contradiction detection, and uncertainty checker for VetVision AI.

Identifies:
- Conflicting symptoms vs physical observations
- Chronological anomalies (duration exceeding pet age)
- Unanalyzed, missing, or low-quality photographs
- Gaps in required vs optional clinical context

SAFETY RULE:
Data quality warnings highlight clinical uncertainty without arbitrarily inflating
or deflating calculated risk scores.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from app.services.risk_engine.evidence import (
    NormalizedEvidence,
    EvidenceStatus,
    EvidenceSource,
    EvidenceItem,
)


@dataclass
class DataQualityWarning:
    """Structured data quality or clinical contradiction warning."""
    code: str
    category: str           # "contradiction", "uncertainty", "chronology", "image_quality"
    severity: str           # "info", "advisory", "warning"
    title: str
    message: str
    conflicting_sources: List[str] = field(default_factory=list)
    clinical_implication: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert warning to dictionary."""
        return {
            "code": self.code,
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "conflicting_sources": self.conflicting_sources,
            "clinical_implication": self.clinical_implication,
        }


class QualityChecker:
    """Evaluates normalized clinical evidence for contradictions and quality gaps."""

    @classmethod
    def check(cls, evidence: NormalizedEvidence) -> List[DataQualityWarning]:
        """Run all data quality audits on normalized clinical evidence."""
        warnings: List[DataQualityWarning] = []

        cls._check_respiratory_contradictions(evidence, warnings)
        cls._check_activity_contradictions(evidence, warnings)
        cls._check_chronological_plausibility(evidence, warnings)
        cls._check_image_quality_status(evidence, warnings)
        cls._check_missing_observations(evidence, warnings)

        return warnings

    @classmethod
    def _check_respiratory_contradictions(
        cls, evidence: NormalizedEvidence, warnings: List[DataQualityWarning]
    ):
        """Check for mismatch between reported respiratory symptoms and breathing observations."""
        resp_symptoms = [
            s for s in evidence.symptoms
            if "breathing" in s.name.lower() or "cough" in s.name.lower() or "respiratory" in (s.details.get("category") or "").lower()
        ]
        breathing_obs = next(
            (o for o in evidence.observations if o.id.startswith("obs_breathing_")),
            None
        )

        if not breathing_obs or breathing_obs.status == EvidenceStatus.UNKNOWN:
            return

        has_severe_dyspnea_symptom = any(
            s.details.get("severity") in ("moderate", "severe") and "difficulty breathing" in s.name.lower()
            for s in resp_symptoms
        )
        obs_is_normal_breathing = breathing_obs.id == "obs_breathing_normal"

        if has_severe_dyspnea_symptom and obs_is_normal_breathing:
            warnings.append(DataQualityWarning(
                code="CONTRADICTION_RESPIRATORY_STATUS",
                category="contradiction",
                severity="warning",
                title="Contradictory Respiratory Findings",
                message=(
                    "Difficulty breathing was reported as an active symptom, but physical "
                    "observations recorded normal, effortless breathing. Triage errs on the "
                    "side of caution and prioritizes the reported dyspnea symptom."
                ),
                conflicting_sources=["symptom_intake", "physical_observation"],
                clinical_implication="Respiratory distress requires in-person veterinary auscultation to resolve conflicting reports.",
            ))

    @classmethod
    def _check_activity_contradictions(
        cls, evidence: NormalizedEvidence, warnings: List[DataQualityWarning]
    ):
        """Check for contradiction between activity observation and reported mobility."""
        activity_obs = next(
            (o for o in evidence.observations if o.id.startswith("obs_activity_")),
            None
        )
        if not activity_obs or activity_obs.status == EvidenceStatus.UNKNOWN:
            return

        is_collapsed = activity_obs.id == "obs_activity_collapse"

        # Check follow-up answers for energetic reports
        for ans in evidence.follow_up_answers:
            ans_text = (ans.display_value or "").lower()
            if is_collapsed and any(w in ans_text for w in ("playful", "active", "normal energy", "energetic")):
                warnings.append(DataQualityWarning(
                    code="CONTRADICTION_ACTIVITY_LEVEL",
                    category="contradiction",
                    severity="warning",
                    title="Contradictory Activity / Mobility Reports",
                    message=(
                        "Physical observation indicates collapse or severe lethargy, whereas "
                        "follow-up answers indicate normal or playful behavior. Clinical evaluation "
                        "prioritizes the more severe observation."
                    ),
                    conflicting_sources=["physical_observation", "adaptive_inquiry"],
                    clinical_implication="Sudden episodic lethargy or collapse warrants immediate veterinary evaluation.",
                ))
                break

    @classmethod
    def _check_chronological_plausibility(
        cls, evidence: NormalizedEvidence, warnings: List[DataQualityWarning]
    ):
        """Check if symptom duration in hours/days exceeds pet's recorded lifespan."""
        pet_age_years = evidence.patient.get("age")
        if pet_age_years is not None and isinstance(pet_age_years, (int, float)) and pet_age_years > 0:
            max_lifespan_hours = pet_age_years * 365.25 * 24.0
            for sym in evidence.symptoms:
                dur_hours = sym.details.get("duration_hours")
                if dur_hours is not None and dur_hours > max_lifespan_hours:
                    warnings.append(DataQualityWarning(
                        code="CHRONOLOGY_DURATION_EXCEEDS_AGE",
                        category="chronology",
                        severity="advisory",
                        title="Symptom Duration Exceeds Pet Age",
                        message=(
                            f"Reported duration for {sym.name} ({dur_hours:.0f} hours) exceeds "
                            f"the pet's recorded age ({pet_age_years} years). Duration has been capped "
                            f"for scoring."
                        ),
                        conflicting_sources=["symptom_intake", "patient_baseline"],
                        clinical_implication="Verification of pet birth date and symptom onset date is advised.",
                    ))

    @classmethod
    def _check_image_quality_status(
        cls, evidence: NormalizedEvidence, warnings: List[DataQualityWarning]
    ):
        """Review computer-vision evidence for quality gate failures or omitted images."""
        poor_quality_imgs = [
            img for img in evidence.image_observations
            if img.id.endswith("_poor_quality")
        ]
        not_provided_imgs = [
            img for img in evidence.image_observations
            if img.id == "img_not_provided"
        ]

        if poor_quality_imgs:
            warnings.append(DataQualityWarning(
                code="IMAGE_QUALITY_INSUFFICIENT",
                category="image_quality",
                severity="info",
                title="Photographic Quality Gate Advisory",
                message=(
                    "One or more uploaded pet images had insufficient lighting, blur, or "
                    "resolution for reliable computer vision feature extraction. The visual inspection "
                    "was excluded from scoring. This does NOT rule out physical skin or mucosal lesions."
                ),
                conflicting_sources=["image_cv"],
                clinical_implication="Direct visual inspection by a veterinary clinician is required.",
            ))
        elif not_provided_imgs:
            warnings.append(DataQualityWarning(
                code="IMAGE_NOT_PROVIDED",
                category="uncertainty",
                severity="info",
                title="Photographic Analysis Omitted",
                message=(
                    "No pet photographs were attached to this intake. Visual dermatological and "
                    "postural inspection was omitted. Lack of photos does not imply lack of visible lesions."
                ),
                conflicting_sources=["image_cv"],
                clinical_implication="Physical physical examination by a veterinarian remains standard of care.",
            ))

    @classmethod
    def _check_missing_observations(
        cls, evidence: NormalizedEvidence, warnings: List[DataQualityWarning]
    ):
        """Surface unrecorded vital observations as clinical uncertainty warnings."""
        if evidence.unknown_fields:
            missing_names = [f.replace("_", " ").title() for f in evidence.unknown_fields if f not in ("image_analysis", "pet_age")]
            if missing_names:
                warnings.append(DataQualityWarning(
                    code="MISSING_OBSERVATION_DATA",
                    category="uncertainty",
                    severity="info",
                    title="Unrecorded Physical Observations",
                    message=(
                        f"The following clinical observations were not recorded during intake: "
                        f"{', '.join(missing_names)}. Incomplete observations are treated as unknown, "
                        f"NOT as negative or healthy baseline findings."
                    ),
                    conflicting_sources=["physical_observation"],
                    clinical_implication="Monitoring appetite, hydration, respiration, and discomfort at home is strongly recommended.",
                ))

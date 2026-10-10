"""Evidence normalization module for VetVision AI Risk Engine.

Provides typed internal representation of clinical evidence, tracking:
- Evidence source (patient baseline, symptom intake, observation, adaptive Q&A, CV image)
- Evidence status (PRESENT, ABSENT, UNKNOWN, CONTRADICTORY)
- Finding description and raw data
- Safe parsing for booleans, strings, nulls, and numeric types

CRITICAL MEDICAL INFORMATICS RULE:
Missing or unrecorded data must NEVER be treated as a negative/normal finding.
It must be explicitly categorized as UNKNOWN.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from datetime import date


class EvidenceSource(str, Enum):
    """Source categorization of clinical evidence."""
    PATIENT_BASELINE = "patient_baseline"
    SYMPTOM_INTAKE = "symptom_intake"
    PHYSICAL_OBSERVATION = "physical_observation"
    ADAPTIVE_INQUIRY = "adaptive_inquiry"
    IMAGE_CV = "image_cv"
    SAFETY_OVERRIDE = "safety_override"


class EvidenceStatus(str, Enum):
    """Presence and certainty status of clinical evidence."""
    PRESENT = "PRESENT"            # Evidence explicitly recorded as observed
    ABSENT = "ABSENT"              # Explicitly recorded as normal or not observed
    UNKNOWN = "UNKNOWN"            # Unrecorded, skipped, or unavailable
    CONTRADICTORY = "CONTRADICTORY"# Multiple conflicting reports recorded


class EvidenceDirection(str, Enum):
    """Directional impact of finding on clinical risk."""
    RISK_INCREASING = "risk_increasing"
    REASSURING = "reassuring"
    UNKNOWN = "unknown"
    EMERGENCY_OVERRIDE = "emergency_override"


@dataclass
class EvidenceItem:
    """Individual typed clinical finding with provenance."""
    id: str
    source: EvidenceSource
    status: EvidenceStatus
    category: str
    name: str
    raw_value: Any
    display_value: str
    direction: EvidenceDirection = EvidenceDirection.UNKNOWN
    notes: Optional[str] = None
    is_emergency_flag: bool = False
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert evidence item to dictionary."""
        return {
            "id": self.id,
            "source": self.source.value,
            "status": self.status.value,
            "category": self.category,
            "name": self.name,
            "raw_value": self.raw_value,
            "display_value": self.display_value,
            "direction": self.direction.value,
            "notes": self.notes,
            "is_emergency_flag": self.is_emergency_flag,
            "details": self.details,
        }


@dataclass
class NormalizedEvidence:
    """Complete structured evidence representation for an assessment."""
    patient: Dict[str, Any]
    items: List[EvidenceItem] = field(default_factory=list)
    symptoms: List[EvidenceItem] = field(default_factory=list)
    observations: List[EvidenceItem] = field(default_factory=list)
    follow_up_answers: List[EvidenceItem] = field(default_factory=list)
    image_observations: List[EvidenceItem] = field(default_factory=list)
    unknown_fields: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_by_source(self, source: EvidenceSource) -> List[EvidenceItem]:
        """Filter items by evidence source."""
        return [item for item in self.items if item.source == source]

    def get_by_status(self, status: EvidenceStatus) -> List[EvidenceItem]:
        """Filter items by evidence status."""
        return [item for item in self.items if item.status == status]


class EvidenceNormalizer:
    """Parses raw AI data payloads into typed, validated NormalizedEvidence."""

    @classmethod
    def normalize(cls, payload: Dict[str, Any]) -> NormalizedEvidence:
        """Main normalization method converting raw dictionary into typed NormalizedEvidence."""
        pet_raw = payload.get("pet") or {}
        symptoms_raw = payload.get("symptoms") or []
        obs_raw = payload.get("observations") or {}
        answers_raw = payload.get("follow_up_answers") or []
        img_raw = payload.get("image_analysis") or {}

        evidence = NormalizedEvidence(patient=pet_raw)

        # 1. Normalize Patient Baseline
        cls._normalize_patient_baseline(pet_raw, evidence)

        # 2. Normalize Symptoms
        cls._normalize_symptoms(symptoms_raw, evidence)

        # 3. Normalize Physical Observations
        cls._normalize_observations(obs_raw, evidence)

        # 4. Normalize Follow-Up Answers
        cls._normalize_follow_up_answers(answers_raw, evidence)

        # 5. Normalize Computer Vision Image Analysis
        cls._normalize_image_analysis(img_raw, evidence)

        return evidence

    @classmethod
    def _normalize_patient_baseline(cls, pet: Dict[str, Any], evidence: NormalizedEvidence):
        """Extract baseline vulnerability evidence."""
        # Age
        age = pet.get("age")
        is_juv = pet.get("is_juvenile")
        is_sen = pet.get("is_senior")
        if is_juv:
            item = EvidenceItem(
                id="pet_age_juvenile",
                source=EvidenceSource.PATIENT_BASELINE,
                status=EvidenceStatus.PRESENT,
                category="demographic",
                name="Juvenile Life Stage",
                raw_value=age,
                display_value="Young pet (< 12 months)",
                direction=EvidenceDirection.RISK_INCREASING,
                notes="Young animals have reduced physiological reserve and dehydrate rapidly",
            )
            evidence.items.append(item)
        elif is_sen:
            item = EvidenceItem(
                id="pet_age_senior",
                source=EvidenceSource.PATIENT_BASELINE,
                status=EvidenceStatus.PRESENT,
                category="demographic",
                name="Senior Life Stage",
                raw_value=age,
                display_value=f"Senior pet ({age} years)",
                direction=EvidenceDirection.RISK_INCREASING,
                notes="Senior pets have higher vulnerability to metabolic and systemic complications",
            )
            evidence.items.append(item)
        elif age is not None:
            item = EvidenceItem(
                id="pet_age_adult",
                source=EvidenceSource.PATIENT_BASELINE,
                status=EvidenceStatus.PRESENT,
                category="demographic",
                name="Adult Life Stage",
                raw_value=age,
                display_value=f"Adult pet ({age} years)",
                direction=EvidenceDirection.REASSURING,
            )
            evidence.items.append(item)
        else:
            evidence.unknown_fields.append("pet_age")

        # Existing chronic conditions
        cond = pet.get("existing_conditions")
        if cond and str(cond).strip() and str(cond).strip().lower() not in ("none", "none reported", "n/a"):
            item = EvidenceItem(
                id="pet_chronic_conditions",
                source=EvidenceSource.PATIENT_BASELINE,
                status=EvidenceStatus.PRESENT,
                category="medical_history",
                name="Pre-existing Conditions",
                raw_value=cond,
                display_value=str(cond).strip(),
                direction=EvidenceDirection.RISK_INCREASING,
                notes="Underlying conditions elevate vulnerability to acute decompensation",
            )
            evidence.items.append(item)

    @classmethod
    def _normalize_symptoms(cls, symptoms: List[Dict[str, Any]], evidence: NormalizedEvidence):
        """Parse reported clinical symptoms."""
        for idx, sym in enumerate(symptoms):
            name = sym.get("name") or "Unnamed Symptom"
            sev = (sym.get("severity") or "mild").lower().strip()
            dur_hours = sym.get("duration_hours")
            dur_dict = sym.get("duration") or {}
            dur_display = (
                f"{dur_dict.get('value')} {dur_dict.get('unit')}"
                if dur_dict.get("value") and dur_dict.get("unit")
                else (f"{dur_hours} hours" if dur_hours is not None else "Duration unknown")
            )

            is_crit = name.lower() in {
                "difficulty breathing", "seizures", "collapse",
                "severe bleeding", "unresponsiveness"
            } and sev in ("moderate", "severe")

            item = EvidenceItem(
                id=f"symptom_{idx}_{name.lower().replace(' ', '_')}",
                source=EvidenceSource.SYMPTOM_INTAKE,
                status=EvidenceStatus.PRESENT,
                category=sym.get("category") or "general",
                name=name,
                raw_value={"severity": sev, "duration_hours": dur_hours},
                display_value=f"{name} ({sev}, duration: {dur_display})",
                direction=EvidenceDirection.RISK_INCREASING,
                is_emergency_flag=is_crit,
                details={
                    "severity": sev,
                    "duration_hours": dur_hours,
                    "duration_display": dur_display,
                    "category": sym.get("category"),
                    "notes": sym.get("notes"),
                },
            )
            evidence.symptoms.append(item)
            evidence.items.append(item)

    @classmethod
    def _normalize_observations(cls, obs: Dict[str, Any], evidence: NormalizedEvidence):
        """Parse behavioral and physiological observations safely supporting booleans and strings."""
        obs = obs or {}

        # 1. Appetite
        appetite = obs.get("appetite")
        if appetite is None or str(appetite).strip() == "":
            evidence.unknown_fields.append("appetite")
            item = EvidenceItem(
                id="obs_appetite_unknown",
                source=EvidenceSource.PHYSICAL_OBSERVATION,
                status=EvidenceStatus.UNKNOWN,
                category="nutrition",
                name="Appetite Status",
                raw_value=None,
                display_value="Not recorded / unknown",
                direction=EvidenceDirection.UNKNOWN,
                notes="Missing appetite data cannot be interpreted as normal eating behavior",
            )
        else:
            val_str = str(appetite).lower().strip()
            if val_str in ("none", "anorexia", "absent"):
                item = EvidenceItem(
                    id="obs_appetite_absent",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.PRESENT,
                    category="nutrition",
                    name="Complete Loss of Appetite",
                    raw_value=appetite,
                    display_value="Anorexia / refusing all food",
                    direction=EvidenceDirection.RISK_INCREASING,
                )
            elif val_str == "decreased":
                item = EvidenceItem(
                    id="obs_appetite_decreased",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.PRESENT,
                    category="nutrition",
                    name="Decreased Appetite",
                    raw_value=appetite,
                    display_value="Eating noticeably less than usual",
                    direction=EvidenceDirection.RISK_INCREASING,
                )
            elif val_str in ("normal", "stable"):
                item = EvidenceItem(
                    id="obs_appetite_normal",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.ABSENT,
                    category="nutrition",
                    name="Normal Appetite",
                    raw_value=appetite,
                    display_value="Eating regularly",
                    direction=EvidenceDirection.REASSURING,
                )
            else:
                item = EvidenceItem(
                    id="obs_appetite_other",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.PRESENT,
                    category="nutrition",
                    name=f"Appetite: {val_str}",
                    raw_value=appetite,
                    display_value=f"Appetite noted as {val_str}",
                    direction=EvidenceDirection.RISK_INCREASING,
                )
        evidence.observations.append(item)
        evidence.items.append(item)

        # 2. Water Intake
        water = obs.get("water_intake")
        if water is None or str(water).strip() == "":
            evidence.unknown_fields.append("water_intake")
            item = EvidenceItem(
                id="obs_water_unknown",
                source=EvidenceSource.PHYSICAL_OBSERVATION,
                status=EvidenceStatus.UNKNOWN,
                category="hydration",
                name="Water Intake Status",
                raw_value=None,
                display_value="Not recorded / unknown",
                direction=EvidenceDirection.UNKNOWN,
            )
        else:
            val_str = str(water).lower().strip()
            if val_str in ("none", "refusing"):
                item = EvidenceItem(
                    id="obs_water_refusing",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.PRESENT,
                    category="hydration",
                    name="Refusal to Drink Water",
                    raw_value=water,
                    display_value="Refusing water (acute dehydration risk)",
                    direction=EvidenceDirection.RISK_INCREASING,
                )
            elif val_str in ("increased", "excessive", "polydipsia"):
                item = EvidenceItem(
                    id="obs_water_increased",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.PRESENT,
                    category="hydration",
                    name="Significantly Increased Thirst",
                    raw_value=water,
                    display_value="Polydipsia / excessive drinking",
                    direction=EvidenceDirection.RISK_INCREASING,
                )
            elif val_str in ("normal", "stable"):
                item = EvidenceItem(
                    id="obs_water_normal",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.ABSENT,
                    category="hydration",
                    name="Normal Hydration Intake",
                    raw_value=water,
                    display_value="Typical water consumption",
                    direction=EvidenceDirection.REASSURING,
                )
            else:
                item = EvidenceItem(
                    id="obs_water_other",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.PRESENT,
                    category="hydration",
                    name=f"Water Intake: {val_str}",
                    raw_value=water,
                    display_value=f"Water intake noted as {val_str}",
                    direction=EvidenceDirection.RISK_INCREASING,
                )
        evidence.observations.append(item)
        evidence.items.append(item)

        # 3. Activity Level
        activity = obs.get("activity_level")
        if activity is None or str(activity).strip() == "":
            evidence.unknown_fields.append("activity_level")
            item = EvidenceItem(
                id="obs_activity_unknown",
                source=EvidenceSource.PHYSICAL_OBSERVATION,
                status=EvidenceStatus.UNKNOWN,
                category="neuromuscular",
                name="Activity Level",
                raw_value=None,
                display_value="Not recorded / unknown",
                direction=EvidenceDirection.UNKNOWN,
            )
        else:
            val_str = str(activity).lower().strip()
            if val_str in ("depressed", "collapse"):
                item = EvidenceItem(
                    id="obs_activity_collapse",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.PRESENT,
                    category="neuromuscular",
                    name="Severe Lethargy / Collapse",
                    raw_value=activity,
                    display_value="Marked depression or inability to rise",
                    direction=EvidenceDirection.RISK_INCREASING,
                )
            elif val_str == "lethargic":
                item = EvidenceItem(
                    id="obs_activity_lethargic",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.PRESENT,
                    category="neuromuscular",
                    name="Lethargy",
                    raw_value=activity,
                    display_value="Noticeably sluggish and unengaged",
                    direction=EvidenceDirection.RISK_INCREASING,
                )
            elif val_str in ("normal", "alert"):
                item = EvidenceItem(
                    id="obs_activity_normal",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.ABSENT,
                    category="neuromuscular",
                    name="Normal Activity",
                    raw_value=activity,
                    display_value="Alert, attentive, and responsive",
                    direction=EvidenceDirection.REASSURING,
                )
            else:
                item = EvidenceItem(
                    id="obs_activity_other",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.PRESENT,
                    category="neuromuscular",
                    name=f"Activity: {val_str}",
                    raw_value=activity,
                    display_value=f"Activity level noted as {val_str}",
                    direction=EvidenceDirection.RISK_INCREASING,
                )
        evidence.observations.append(item)
        evidence.items.append(item)

        # 4. Breathing Change
        breathing = obs.get("breathing_change")
        if breathing is None or str(breathing).strip() == "":
            evidence.unknown_fields.append("breathing_change")
            item = EvidenceItem(
                id="obs_breathing_unknown",
                source=EvidenceSource.PHYSICAL_OBSERVATION,
                status=EvidenceStatus.UNKNOWN,
                category="respiratory",
                name="Respiratory Effort",
                raw_value=None,
                display_value="Not recorded / unknown",
                direction=EvidenceDirection.UNKNOWN,
            )
        else:
            val_str = str(breathing).lower().strip()
            if val_str in ("labored", "wheezing"):
                item = EvidenceItem(
                    id="obs_breathing_labored",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.PRESENT,
                    category="respiratory",
                    name="Labored Breathing / Wheezing",
                    raw_value=breathing,
                    display_value="Labored, open-mouth, or wheezing respiration",
                    direction=EvidenceDirection.EMERGENCY_OVERRIDE,
                    is_emergency_flag=True,
                )
            elif val_str in ("rapid", "shallow"):
                item = EvidenceItem(
                    id="obs_breathing_rapid",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.PRESENT,
                    category="respiratory",
                    name="Elevated Respiratory Rate",
                    raw_value=breathing,
                    display_value="Tachypnea / abnormally rapid breathing",
                    direction=EvidenceDirection.RISK_INCREASING,
                )
            elif val_str in ("normal", "regular", "effortless"):
                item = EvidenceItem(
                    id="obs_breathing_normal",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.ABSENT,
                    category="respiratory",
                    name="Normal Breathing",
                    raw_value=breathing,
                    display_value="Smooth, effortless respiration",
                    direction=EvidenceDirection.REASSURING,
                )
            else:
                item = EvidenceItem(
                    id="obs_breathing_other",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.PRESENT,
                    category="respiratory",
                    name=f"Breathing: {val_str}",
                    raw_value=breathing,
                    display_value=f"Respiration change noted as {val_str}",
                    direction=EvidenceDirection.RISK_INCREASING,
                )
        evidence.observations.append(item)
        evidence.items.append(item)

        # 5. Pain Observed (CRITICAL: safely handle bool, string, null)
        raw_pain = obs.get("pain_observed")
        if raw_pain is None:
            evidence.unknown_fields.append("pain_observed")
        pain_item = cls._parse_pain_observation(raw_pain)
        evidence.observations.append(pain_item)
        evidence.items.append(pain_item)

        # 6. Elimination: Stool & Urine (if present)
        for elim_key, elim_cat in [("stool_change", "gastrointestinal"), ("urine_change", "urinary")]:
            elim_val = obs.get(elim_key)
            if elim_val and str(elim_val).strip() and str(elim_val).strip().lower() not in ("normal", "none"):
                item = EvidenceItem(
                    id=f"obs_{elim_key}",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.PRESENT,
                    category=elim_cat,
                    name=elim_key.replace("_", " ").title(),
                    raw_value=elim_val,
                    display_value=str(elim_val).strip(),
                    direction=EvidenceDirection.RISK_INCREASING,
                )
                evidence.observations.append(item)
                evidence.items.append(item)

    @classmethod
    def _parse_pain_observation(cls, raw_pain: Any) -> EvidenceItem:
        """Safely parse pain observation across boolean, string, or null values."""
        if raw_pain is None:
            return EvidenceItem(
                id="obs_pain_unknown",
                source=EvidenceSource.PHYSICAL_OBSERVATION,
                status=EvidenceStatus.UNKNOWN,
                category="discomfort",
                name="Pain Evaluation",
                raw_value=None,
                display_value="Not recorded / unknown",
                direction=EvidenceDirection.UNKNOWN,
            )

        # Handle boolean True / False
        if isinstance(raw_pain, bool):
            if raw_pain:
                return EvidenceItem(
                    id="obs_pain_boolean_true",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.PRESENT,
                    category="discomfort",
                    name="Visible Pain Signs",
                    raw_value=True,
                    display_value="Signs of acute pain observed by owner",
                    direction=EvidenceDirection.RISK_INCREASING,
                    details={"pain_severity": "moderate"},
                )
            else:
                return EvidenceItem(
                    id="obs_pain_boolean_false",
                    source=EvidenceSource.PHYSICAL_OBSERVATION,
                    status=EvidenceStatus.ABSENT,
                    category="discomfort",
                    name="No Pain Observed",
                    raw_value=False,
                    display_value="No signs of physical pain reported",
                    direction=EvidenceDirection.REASSURING,
                    details={"pain_severity": "none"},
                )

        # Handle string input
        val_str = str(raw_pain).lower().strip()
        if val_str in ("severe", "intense", "extreme"):
            return EvidenceItem(
                id="obs_pain_severe",
                source=EvidenceSource.PHYSICAL_OBSERVATION,
                status=EvidenceStatus.PRESENT,
                category="discomfort",
                name="Severe Pain / Acute Distress",
                raw_value=raw_pain,
                display_value="Severe signs of physical pain reported",
                direction=EvidenceDirection.EMERGENCY_OVERRIDE,
                is_emergency_flag=True,
                details={"pain_severity": "severe"},
            )
        elif val_str in ("moderate", "true", "yes", "observed"):
            return EvidenceItem(
                id="obs_pain_moderate",
                source=EvidenceSource.PHYSICAL_OBSERVATION,
                status=EvidenceStatus.PRESENT,
                category="discomfort",
                name="Moderate Pain Observed",
                raw_value=raw_pain,
                display_value="Moderate signs of physical pain reported",
                direction=EvidenceDirection.RISK_INCREASING,
                details={"pain_severity": "moderate"},
            )
        elif val_str in ("mild", "slight"):
            return EvidenceItem(
                id="obs_pain_mild",
                source=EvidenceSource.PHYSICAL_OBSERVATION,
                status=EvidenceStatus.PRESENT,
                category="discomfort",
                name="Mild Pain Observed",
                raw_value=raw_pain,
                display_value="Mild signs of discomfort reported",
                direction=EvidenceDirection.RISK_INCREASING,
                details={"pain_severity": "mild"},
            )
        elif val_str in ("none", "false", "no", "absent", "normal"):
            return EvidenceItem(
                id="obs_pain_none",
                source=EvidenceSource.PHYSICAL_OBSERVATION,
                status=EvidenceStatus.ABSENT,
                category="discomfort",
                name="No Pain Observed",
                raw_value=raw_pain,
                display_value="No signs of physical pain reported",
                direction=EvidenceDirection.REASSURING,
                details={"pain_severity": "none"},
            )

        # Fallback unexpected string/number
        return EvidenceItem(
            id="obs_pain_other",
            source=EvidenceSource.PHYSICAL_OBSERVATION,
            status=EvidenceStatus.PRESENT,
            category="discomfort",
            name=f"Pain Status: {val_str}",
            raw_value=raw_pain,
            display_value=f"Pain recorded as {val_str}",
            direction=EvidenceDirection.RISK_INCREASING,
            details={"pain_severity": "moderate"},
        )

    @classmethod
    def _normalize_follow_up_answers(
        cls, answers: List[Dict[str, Any]], evidence: NormalizedEvidence
    ):
        """Parse adaptive Q&A responses."""
        for idx, ans in enumerate(answers):
            q_text = ans.get("question") or "Follow-up question"
            opt_text = ans.get("answer_option") or ans.get("answer_text") or "Recorded"
            opt_val = (ans.get("answer_option_value") or "").lower()
            triggered_em = ans.get("triggered_emergency", False)
            weight = ans.get("severity_weight")

            combined_text = f"{opt_val} {opt_text}".lower()
            is_worsening = any(t in combined_text for t in ("worsen", "worse", "increasing", "severe"))

            direction = EvidenceDirection.RISK_INCREASING if (is_worsening or triggered_em or (weight and weight > 0)) else EvidenceDirection.REASSURING

            item = EvidenceItem(
                id=f"answer_{idx}",
                source=EvidenceSource.ADAPTIVE_INQUIRY,
                status=EvidenceStatus.PRESENT,
                category=ans.get("category") or "clinical_inquiry",
                name=q_text,
                raw_value=ans,
                display_value=f"{q_text}: {opt_text}",
                direction=direction,
                is_emergency_flag=triggered_em,
                details={
                    "severity_weight": weight,
                    "answer_option": opt_text,
                    "triggered_emergency": triggered_em,
                    "is_worsening": is_worsening,
                },
            )
            evidence.follow_up_answers.append(item)
            evidence.items.append(item)

    @classmethod
    def _normalize_image_analysis(
        cls, img_analysis: Dict[str, Any], evidence: NormalizedEvidence
    ):
        """Parse computer-vision observations respecting quality gates and missing states."""
        images_count = img_analysis.get("images_count", 0)
        analyzed_count = img_analysis.get("analyzed_count", 0)
        observations = img_analysis.get("observations") or []

        if images_count == 0:
            evidence.unknown_fields.append("image_analysis")
            item = EvidenceItem(
                id="img_not_provided",
                source=EvidenceSource.IMAGE_CV,
                status=EvidenceStatus.UNKNOWN,
                category="visual_inspection",
                name="Pet Image Analysis",
                raw_value=None,
                display_value="No photographic inspection attached (optional)",
                direction=EvidenceDirection.UNKNOWN,
                notes="Absence of uploaded photos does not imply absence of visual abnormalities",
            )
            evidence.image_observations.append(item)
            evidence.items.append(item)
            return

        for idx, obs in enumerate(observations):
            label = obs.get("observation_label", "")
            sev = (obs.get("severity") or "normal").lower()

            if label == "POOR_IMAGE_QUALITY":
                item = EvidenceItem(
                    id=f"img_obs_{idx}_poor_quality",
                    source=EvidenceSource.IMAGE_CV,
                    status=EvidenceStatus.UNKNOWN,
                    category="visual_inspection",
                    name="Image Quality Gate",
                    raw_value=obs,
                    display_value="Attached photo has insufficient resolution/lighting for diagnostic inspection",
                    direction=EvidenceDirection.UNKNOWN,
                    notes="Poor image quality cannot confirm or rule out visual symptoms",
                )
            elif label == "ELEVATED_ERYTHEMA_DETECTED":
                item = EvidenceItem(
                    id=f"img_obs_{idx}_erythema",
                    source=EvidenceSource.IMAGE_CV,
                    status=EvidenceStatus.PRESENT,
                    category="visual_inspection",
                    name="Visual Erythema / Redness",
                    raw_value=obs,
                    display_value=f"Elevated localized erythema detected by computer vision ({sev})",
                    direction=EvidenceDirection.RISK_INCREASING,
                    details={"severity": sev},
                )
            else:
                item = EvidenceItem(
                    id=f"img_obs_{idx}_{label.lower()}",
                    source=EvidenceSource.IMAGE_CV,
                    status=EvidenceStatus.PRESENT,
                    category="visual_inspection",
                    name=label.replace("_", " ").title(),
                    raw_value=obs,
                    display_value=f"Visual pattern detected: {label} ({sev})",
                    direction=EvidenceDirection.RISK_INCREASING if sev in ("moderate", "severe") else EvidenceDirection.UNKNOWN,
                    details={"severity": sev},
                )

            evidence.image_observations.append(item)
            evidence.items.append(item)

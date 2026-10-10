"""Rule-based explainable health risk analysis engine.

Provides transparent clinical heuristic scoring based on pet baseline,
symptoms, duration, observations, follow-up answers, and emergency indicators.
Upgraded in Step 8A with:
- Typed evidence normalization (EvidenceNormalizer)
- Contradiction & data-quality audit (QualityChecker)
- Structured factor attribution with source, status, direction, and rule rationale
- Type-safe handling for booleans, strings, nulls, and unexpected types
- Strict emergency hard-stop preservation (score floor >= 90)
"""
from typing import Dict, Any, List, Tuple, Optional
from app.services.risk_engine.base import BaseRiskAnalysisEngine, RiskAnalysisOutput
from app.services.risk_engine.evidence import (
    EvidenceNormalizer,
    NormalizedEvidence,
    EvidenceSource,
    EvidenceStatus,
    EvidenceDirection,
)
from app.services.risk_engine.quality_checker import QualityChecker, DataQualityWarning
from app.services.risk_engine.structured_factor import StructuredFactor
from app.services.emergency_service import EmergencyAssessmentService


class RuleBasedRiskAnalysisEngine(BaseRiskAnalysisEngine):
    """Clinical heuristic scoring engine with transparent explainability.

    Scoring Tiers:
    - LOW: 0–29
    - MODERATE: 30–59
    - HIGH: 60–84
    - EMERGENCY: 85–100 (or acute emergency hard-stop trigger with floor 90)

    Theoretical Sub-Score Maximums:
    - Symptom severity: 55 pts
    - Duration chronicity: 18 pts
    - Physical observations: 30 pts
    - Follow-up dynamic answers: 25 pts
    - Vulnerability modifier: 15 pts
    - Image observations: 8 pts
    Sum = 151 pts, clamped strictly to [0, 100].
    """

    ENGINE_VERSION = "v1.0.0-rule_hybrid"
    RULESET_VERSION = "v1.1.0-evidence_explainability"

    # Base symptom severity weights
    SEVERITY_WEIGHTS = {
        "mild": 12,
        "moderate": 28,
        "severe": 45,
    }

    @property
    def version(self) -> str:
        return self.ENGINE_VERSION

    def analyze(self, payload: Dict[str, Any]) -> RiskAnalysisOutput:
        """Run explainable risk analysis on structured AI payload."""
        # 1. Normalize Evidence into Typed Representation
        evidence: NormalizedEvidence = EvidenceNormalizer.normalize(payload)

        # 2. Run Data Quality and Contradiction Audits
        quality_warnings: List[DataQualityWarning] = QualityChecker.check(evidence)
        warning_dicts = [w.to_dict() for w in quality_warnings]

        # 3. Emergency Screening Authority (Steps 2 & 3 Integration)
        emergency_eval = EmergencyAssessmentService.evaluate_payload(payload)
        is_emergency = emergency_eval.get("is_emergency_flagged", False)
        emergency_flags = emergency_eval.get("flags", [])

        key_factors: List[str] = []
        structured_factors: List[StructuredFactor] = []
        factor_breakdown: Dict[str, Any] = {}

        # 4. Calculate Sub-Scores and Structured Factor Attribution
        # 4a. Symptom Score (Max 55 pts)
        sym_score, sym_factors, struct_sym_factors = self._calculate_symptom_score(evidence)
        key_factors.extend(sym_factors)
        structured_factors.extend(struct_sym_factors)
        factor_breakdown["symptom_score"] = sym_score

        # 4b. Duration Score (Max 18 pts)
        dur_score, dur_factors, struct_dur_factors = self._calculate_duration_score(evidence)
        key_factors.extend(dur_factors)
        structured_factors.extend(struct_dur_factors)
        factor_breakdown["duration_score"] = dur_score

        # 4c. Physical Observations Score (Max 30 pts)
        obs_score, obs_factors, struct_obs_factors = self._calculate_observation_score(evidence)
        key_factors.extend(obs_factors)
        structured_factors.extend(struct_obs_factors)
        factor_breakdown["observation_score"] = obs_score

        # 4d. Dynamic Follow-Up Answers Score (Max 25 pts)
        ans_score, ans_factors, struct_ans_factors = self._calculate_answers_score(evidence)
        key_factors.extend(ans_factors)
        structured_factors.extend(struct_ans_factors)
        factor_breakdown["follow_up_score"] = ans_score

        # 4e. Patient Vulnerability Modifier (Max 15 pts)
        vuln_score, vuln_factors, struct_vuln_factors = self._calculate_vulnerability_score(evidence)
        key_factors.extend(vuln_factors)
        structured_factors.extend(struct_vuln_factors)
        factor_breakdown["vulnerability_modifier"] = vuln_score

        # 4f. Computer Vision Image Observations (Max 8 pts)
        img_score, img_factors, struct_img_factors = self._calculate_image_score(evidence)
        key_factors.extend(img_factors)
        structured_factors.extend(struct_img_factors)
        factor_breakdown["image_score"] = img_score

        # 5. Raw Score Summation & Clamping [0, 100]
        raw_score = sym_score + dur_score + obs_score + ans_score + vuln_score + img_score
        calculated_score = min(100, max(0, raw_score))
        factor_breakdown["raw_calculated_score"] = calculated_score

        # 6. Apply Emergency Hard-Stop Rule
        factor_breakdown["emergency_override"] = False

        if is_emergency or emergency_flags:
            is_emergency = True
            risk_level = "EMERGENCY"
            risk_score = max(calculated_score, 90)
            factor_breakdown["emergency_override"] = True

            emergency_descriptions = [f"CRITICAL: {flag}" for flag in emergency_flags]
            key_factors = emergency_descriptions + [f for f in key_factors if f not in emergency_descriptions]

            # Prepend emergency structured factors
            for flag in emergency_flags:
                structured_factors.insert(0, StructuredFactor(
                    factor_name="Emergency Hard-Stop Trigger",
                    finding=flag,
                    source=EvidenceSource.SAFETY_OVERRIDE.value,
                    status=EvidenceStatus.PRESENT.value,
                    direction=EvidenceDirection.EMERGENCY_OVERRIDE.value,
                    rule_applied="Clinical safety override enforces triage floor score >= 90",
                    rationale="Critical signs bypass routine additive scoring to protect patient life safety.",
                    contribution_pts=None,  # Not an additive contribution, but a safety floor
                    is_emergency_flag=True,
                ))
        else:
            risk_score = calculated_score
            if risk_score >= 85:
                risk_level = "EMERGENCY"
            elif risk_score >= 60:
                risk_level = "HIGH"
            elif risk_score >= 30:
                risk_level = "MODERATE"
            else:
                risk_level = "LOW"

        # 7. Generate Recommendation
        recommendation = self._generate_recommendation(risk_level, is_emergency)

        # 8. Deduplicate Key Factors
        seen_factors = set()
        deduped_factors: List[str] = []
        for factor in key_factors:
            if factor and factor not in seen_factors:
                seen_factors.add(factor)
                deduped_factors.append(factor)

        if not deduped_factors:
            deduped_factors.append("Mild symptoms with stable physiological observations")

        # 9. Store Metadata in factor_breakdown
        factor_breakdown["ruleset_version"] = self.RULESET_VERSION
        factor_breakdown["structured_factors"] = [f.to_dict() for f in structured_factors]
        factor_breakdown["data_quality_warnings"] = warning_dicts
        factor_breakdown["unknown_evidence_fields"] = evidence.unknown_fields
        factor_breakdown["evidence_summary"] = {
            "symptoms_reported": len(evidence.symptoms),
            "observations_recorded": len([o for o in evidence.observations if o.status != EvidenceStatus.UNKNOWN]),
            "unknown_fields_count": len(evidence.unknown_fields),
            "contradiction_warnings_count": len([w for w in quality_warnings if w.category == "contradiction"]),
        }

        return RiskAnalysisOutput(
            risk_level=risk_level,
            risk_score=risk_score,
            key_factors=deduped_factors[:6],
            factor_breakdown=factor_breakdown,
            structured_factors=[f.to_dict() for f in structured_factors],
            data_quality_warnings=warning_dicts,
            recommendation=recommendation,
            is_emergency=is_emergency,
            engine_version=self.ENGINE_VERSION,
        )

    def _calculate_symptom_score(
        self, evidence: NormalizedEvidence
    ) -> Tuple[int, List[str], List[StructuredFactor]]:
        """Calculate score and structured factors from reported symptoms."""
        symptoms = evidence.symptoms
        if not symptoms:
            return 0, [], []

        factors: List[str] = []
        struct_factors: List[StructuredFactor] = []
        weights: List[Tuple[int, str, str]] = []

        for sym in symptoms:
            sev = (sym.details.get("severity") or "mild").lower()
            w = self.SEVERITY_WEIGHTS.get(sev, 12)
            name = sym.name
            weights.append((w, name, sev))

        weights.sort(key=lambda x: x[0], reverse=True)
        primary_w, primary_name, primary_sev = weights[0]

        # Primary symptom factor
        struct_factors.append(StructuredFactor(
            factor_name="Primary Symptom Severity",
            finding=f"{primary_name} ({primary_sev})",
            source=EvidenceSource.SYMPTOM_INTAKE.value,
            status=EvidenceStatus.PRESENT.value,
            direction=EvidenceDirection.RISK_INCREASING.value,
            rule_applied=f"Primary symptom assigned severity base weight of {primary_w} pts",
            rationale=f"Primary complaint of {primary_name} defines the acute clinical presentation.",
            contribution_pts=primary_w,
        ))

        if primary_sev == "severe":
            factors.append(f"Severe primary symptom: {primary_name}")
        elif primary_sev == "moderate":
            factors.append(f"Moderate symptom: {primary_name}")

        # Diminishing weight for additional co-occurring symptoms
        additional_score = 0
        if len(weights) > 1:
            for w, name, sev in weights[1:]:
                inc = round(w * 0.4)
                additional_score += inc
                struct_factors.append(StructuredFactor(
                    factor_name="Co-Occurring Symptom",
                    finding=f"{name} ({sev})",
                    source=EvidenceSource.SYMPTOM_INTAKE.value,
                    status=EvidenceStatus.PRESENT,
                    direction=EvidenceDirection.RISK_INCREASING.value,
                    rule_applied=f"Co-occurring symptom assigned diminishing weight (40% of {w} = +{inc} pts)",
                    rationale=f"Multiple concurrent clinical signs indicate broader physiological impact.",
                    contribution_pts=inc,
                ))

            additional_capped = min(20, additional_score)
            factors.append(f"Multiple co-occurring symptoms ({len(weights)} symptoms reported)")

        total_symptom_score = min(55, primary_w + min(20, additional_score))
        return total_symptom_score, factors, struct_factors

    def _calculate_duration_score(
        self, evidence: NormalizedEvidence
    ) -> Tuple[int, List[str], List[StructuredFactor]]:
        """Calculate score and structured factors from symptom duration."""
        symptoms = evidence.symptoms
        if not symptoms:
            return 0, [], []

        max_hours = 0.0
        max_sym_name = ""
        for sym in symptoms:
            dur = sym.details.get("duration_hours")
            if dur is not None and dur > max_hours:
                max_hours = dur
                max_sym_name = sym.name

        factors: List[str] = []
        struct_factors: List[StructuredFactor] = []
        duration_score = 0

        if max_hours >= 168.0:
            duration_score = 18
            finding_text = f"Persistent chronic duration ({max_hours/24:.1f} days for {max_sym_name})"
            factors.append("Symptoms persisting chronically for more than 1 week")
            struct_factors.append(StructuredFactor(
                factor_name="Chronic Symptom Duration",
                finding=finding_text,
                source=EvidenceSource.SYMPTOM_INTAKE.value,
                status=EvidenceStatus.PRESENT.value,
                direction=EvidenceDirection.RISK_INCREASING.value,
                rule_applied="Duration >= 168 hours (+18 pts)",
                rationale="Chronic persistence (> 7 days) elevates risk of secondary systemic deterioration.",
                contribution_pts=18,
            ))
        elif max_hours >= 72.0:
            duration_score = 12
            finding_text = f"Multi-day duration ({max_hours/24:.1f} days for {max_sym_name})"
            factors.append("Symptoms persisting for several days (3–7 days)")
            struct_factors.append(StructuredFactor(
                factor_name="Prolonged Symptom Duration",
                finding=finding_text,
                source=EvidenceSource.SYMPTOM_INTAKE.value,
                status=EvidenceStatus.PRESENT.value,
                direction=EvidenceDirection.RISK_INCREASING.value,
                rule_applied="Duration between 72 and 168 hours (+12 pts)",
                rationale="Symptoms persisting 3 to 7 days warrant formal clinical evaluation.",
                contribution_pts=12,
            ))
        elif max_hours >= 24.0:
            duration_score = 6
            finding_text = f"Duration between 24 and 72 hours for {max_sym_name}"
            factors.append("Symptoms persisting between 24 and 72 hours")
            struct_factors.append(StructuredFactor(
                factor_name="Moderate Symptom Duration",
                finding=finding_text,
                source=EvidenceSource.SYMPTOM_INTAKE.value,
                status=EvidenceStatus.PRESENT.value,
                direction=EvidenceDirection.RISK_INCREASING.value,
                rule_applied="Duration between 24 and 72 hours (+6 pts)",
                rationale="Symptoms crossing 24 hours indicate failure of immediate spontaneous resolution.",
                contribution_pts=6,
            ))
        elif max_hours > 0.0 and any(s.details.get("severity") in ("moderate", "severe") for s in symptoms):
            duration_score = 3
            factors.append("Acute symptom onset (< 24 hours)")
            struct_factors.append(StructuredFactor(
                factor_name="Acute Symptom Onset",
                finding=f"Acute onset (< 24 hours) with moderate/severe signs",
                source=EvidenceSource.SYMPTOM_INTAKE.value,
                status=EvidenceStatus.PRESENT.value,
                direction=EvidenceDirection.RISK_INCREASING.value,
                rule_applied="Acute onset with moderate/severe severity (+3 pts)",
                rationale="Rapid acute manifestation indicates active pathological progression.",
                contribution_pts=3,
            ))

        return duration_score, factors, struct_factors

    def _calculate_observation_score(
        self, evidence: NormalizedEvidence
    ) -> Tuple[int, List[str], List[StructuredFactor]]:
        """Calculate physical observation scores with type safety."""
        score = 0
        factors: List[str] = []
        struct_factors: List[StructuredFactor] = []

        # Find observation items
        obs_map = {o.id: o for o in evidence.observations}

        # 1. Appetite
        for oid, pts, label, rat in [
            ("obs_appetite_absent", 14, "Complete loss of appetite / anorexia", "Complete anorexia causes rapid hepatic lipidosis risk (in cats) and hypoglycemia."),
            ("obs_appetite_decreased", 6, "Decreased food intake observed", "Decreased caloric intake reflects metabolic discomfort or nausea."),
        ]:
            if oid in obs_map and obs_map[oid].status == EvidenceStatus.PRESENT:
                score += pts
                factors.append(label)
                struct_factors.append(StructuredFactor(
                    factor_name="Appetite Observation",
                    finding=obs_map[oid].display_value,
                    source=EvidenceSource.PHYSICAL_OBSERVATION.value,
                    status=EvidenceStatus.PRESENT.value,
                    direction=EvidenceDirection.RISK_INCREASING.value,
                    rule_applied=f"{label} (+{pts} pts)",
                    rationale=rat,
                    contribution_pts=pts,
                ))

        # 2. Water Intake
        for oid, pts, label, rat in [
            ("obs_water_refusing", 14, "Refusal to drink water (acute dehydration risk)", "Adipsia accelerates acute hypovolemia and dehydration."),
            ("obs_water_increased", 6, "Polydipsia / significantly increased thirst", "Polydipsia can signal renal compromise, diabetes, or endocrine strain."),
        ]:
            if oid in obs_map and obs_map[oid].status == EvidenceStatus.PRESENT:
                score += pts
                factors.append(label)
                struct_factors.append(StructuredFactor(
                    factor_name="Hydration Observation",
                    finding=obs_map[oid].display_value,
                    source=EvidenceSource.PHYSICAL_OBSERVATION.value,
                    status=EvidenceStatus.PRESENT.value,
                    direction=EvidenceDirection.RISK_INCREASING.value,
                    rule_applied=f"{label} (+{pts} pts)",
                    rationale=rat,
                    contribution_pts=pts,
                ))

        # 3. Activity Level
        for oid, pts, label, rat in [
            ("obs_activity_collapse", 16, "Marked depression or collapse in activity", "Severe depression or collapse reflects central nervous system or circulatory compromise."),
            ("obs_activity_lethargic", 10, "Noticeable lethargy and sluggishness", "Generalized lethargy signals systemic inflammatory or infectious burden."),
        ]:
            if oid in obs_map and obs_map[oid].status == EvidenceStatus.PRESENT:
                score += pts
                factors.append(label)
                struct_factors.append(StructuredFactor(
                    factor_name="Activity Observation",
                    finding=obs_map[oid].display_value,
                    source=EvidenceSource.PHYSICAL_OBSERVATION.value,
                    status=EvidenceStatus.PRESENT.value,
                    direction=EvidenceDirection.RISK_INCREASING.value,
                    rule_applied=f"{label} (+{pts} pts)",
                    rationale=rat,
                    contribution_pts=pts,
                ))

        # 4. Respiration
        if "obs_breathing_labored" in obs_map and obs_map["obs_breathing_labored"].status == EvidenceStatus.PRESENT:
            score += 25
            factors.append("Abnormal respiratory effort: labored breathing / wheezing")
            struct_factors.append(StructuredFactor(
                factor_name="Respiratory Effort",
                finding=obs_map["obs_breathing_labored"].display_value,
                source=EvidenceSource.PHYSICAL_OBSERVATION.value,
                status=EvidenceStatus.PRESENT.value,
                direction=EvidenceDirection.EMERGENCY_OVERRIDE.value,
                rule_applied="Labored breathing (+25 pts & emergency hard-stop)",
                rationale="Labored respiration creates immediate hypoxia risk requiring urgent stabilization.",
                contribution_pts=25,
                is_emergency_flag=True,
            ))
        elif "obs_breathing_rapid" in obs_map and obs_map["obs_breathing_rapid"].status == EvidenceStatus.PRESENT:
            score += 12
            factors.append("Tachypnea / abnormally rapid breathing")
            struct_factors.append(StructuredFactor(
                factor_name="Respiratory Effort",
                finding=obs_map["obs_breathing_rapid"].display_value,
                source=EvidenceSource.PHYSICAL_OBSERVATION.value,
                status=EvidenceStatus.PRESENT.value,
                direction=EvidenceDirection.RISK_INCREASING.value,
                rule_applied="Rapid breathing tachypnea (+12 pts)",
                rationale="Tachypnea may indicate pain, fever, or early respiratory compensation.",
                contribution_pts=12,
            ))

        # 5. Pain Observation (Handles boolean True, "severe", "moderate", "mild")
        pain_item = next((o for o in evidence.observations if o.id.startswith("obs_pain_") and o.status == EvidenceStatus.PRESENT), None)
        if pain_item:
            sev = pain_item.details.get("pain_severity") or "moderate"
            if sev == "severe" or pain_item.id == "obs_pain_severe":
                score += 22
                factors.append("Severe signs of physical pain or distress")
                struct_factors.append(StructuredFactor(
                    factor_name="Pain Observation",
                    finding=pain_item.display_value,
                    source=EvidenceSource.PHYSICAL_OBSERVATION.value,
                    status=EvidenceStatus.PRESENT.value,
                    direction=EvidenceDirection.EMERGENCY_OVERRIDE.value,
                    rule_applied="Severe pain observation (+22 pts & urgent evaluation)",
                    rationale="Severe acute pain requires immediate clinical analgesia and source diagnostic.",
                    contribution_pts=22,
                    is_emergency_flag=True,
                ))
            elif sev == "moderate" or pain_item.id in ("obs_pain_moderate", "obs_pain_boolean_true"):
                score += 12
                factors.append("Moderate signs of pain or discomfort")
                struct_factors.append(StructuredFactor(
                    factor_name="Pain Observation",
                    finding=pain_item.display_value,
                    source=EvidenceSource.PHYSICAL_OBSERVATION.value,
                    status=EvidenceStatus.PRESENT.value,
                    direction=EvidenceDirection.RISK_INCREASING.value,
                    rule_applied="Moderate pain observed (+12 pts)",
                    rationale="Observable discomfort indicates active musculoskeletal or visceral inflammation.",
                    contribution_pts=12,
                ))
            elif sev == "mild" or pain_item.id == "obs_pain_mild":
                score += 5
                struct_factors.append(StructuredFactor(
                    factor_name="Pain Observation",
                    finding=pain_item.display_value,
                    source=EvidenceSource.PHYSICAL_OBSERVATION.value,
                    status=EvidenceStatus.PRESENT.value,
                    direction=EvidenceDirection.RISK_INCREASING.value,
                    rule_applied="Mild pain observed (+5 pts)",
                    rationale="Mild discomfort noted during examination.",
                    contribution_pts=5,
                ))

        # 6. Elimination Patterns
        if "obs_stool_change" in obs_map and obs_map["obs_stool_change"].status == EvidenceStatus.PRESENT:
            score += 8
            val = obs_map["obs_stool_change"].display_value
            factors.append(f"Abnormal stool changes noted: {val}")
            struct_factors.append(StructuredFactor(
                factor_name="Gastrointestinal Elimination",
                finding=val,
                source=EvidenceSource.PHYSICAL_OBSERVATION.value,
                status=EvidenceStatus.PRESENT.value,
                direction=EvidenceDirection.RISK_INCREASING.value,
                rule_applied="Abnormal stool pattern (+8 pts)",
                rationale="Altered stool indicates enteric irritation or malabsorption.",
                contribution_pts=8,
            ))

        if "obs_urine_change" in obs_map and obs_map["obs_urine_change"].status == EvidenceStatus.PRESENT:
            score += 10
            val = obs_map["obs_urine_change"].display_value
            factors.append(f"Abnormal urinary pattern noted: {val}")
            struct_factors.append(StructuredFactor(
                factor_name="Urinary Pattern",
                finding=val,
                source=EvidenceSource.PHYSICAL_OBSERVATION.value,
                status=EvidenceStatus.PRESENT.value,
                direction=EvidenceDirection.RISK_INCREASING.value,
                rule_applied="Abnormal urinary pattern (+10 pts)",
                rationale="Altered urination can signal lower urinary tract infection or obstruction.",
                contribution_pts=10,
            ))

        # Add Reassuring Physical Factors if Present
        if "obs_breathing_normal" in obs_map and obs_map["obs_breathing_normal"].status == EvidenceStatus.ABSENT:
            struct_factors.append(StructuredFactor(
                factor_name="Respiratory Effort",
                finding="Normal, effortless breathing",
                source=EvidenceSource.PHYSICAL_OBSERVATION.value,
                status=EvidenceStatus.ABSENT.value,
                direction=EvidenceDirection.REASSURING.value,
                rule_applied="Eupneic respiration baseline",
                rationale="Effortless breathing indicates absence of acute airway obstruction.",
                contribution_pts=0,
            ))

        return min(30, score), factors, struct_factors

    def _calculate_answers_score(
        self, evidence: NormalizedEvidence
    ) -> Tuple[int, List[str], List[StructuredFactor]]:
        """Calculate dynamic follow-up answers score."""
        score = 0
        factors: List[str] = []
        struct_factors: List[StructuredFactor] = []

        for ans in evidence.follow_up_answers:
            pts_for_ans = 0
            weight = ans.details.get("severity_weight")
            if weight is not None and isinstance(weight, (int, float)):
                pts_for_ans += round(weight * 12)

            is_worsening = ans.details.get("is_worsening", False)
            if is_worsening:
                pts_for_ans += 5
                factors.append("Follow-up response indicates worsening clinical condition")

            if pts_for_ans > 0:
                score += pts_for_ans
                struct_factors.append(StructuredFactor(
                    factor_name="Follow-Up Clinical Inquiry",
                    finding=ans.display_value,
                    source=EvidenceSource.ADAPTIVE_INQUIRY.value,
                    status=EvidenceStatus.PRESENT.value,
                    direction=EvidenceDirection.RISK_INCREASING.value,
                    rule_applied=f"Dynamic follow-up answer weight (+{pts_for_ans} pts)",
                    rationale="Owner response during adaptive inquiry confirmed heightened clinical severity.",
                    contribution_pts=pts_for_ans,
                    is_emergency_flag=ans.is_emergency_flag,
                ))

        return min(25, score), factors, struct_factors

    def _calculate_vulnerability_score(
        self, evidence: NormalizedEvidence
    ) -> Tuple[int, List[str], List[StructuredFactor]]:
        """Calculate patient baseline vulnerability score."""
        score = 0
        factors: List[str] = []
        struct_factors: List[StructuredFactor] = []

        pet = evidence.patient
        is_juv = pet.get("is_juvenile")
        is_sen = pet.get("is_senior")
        cond = pet.get("existing_conditions")

        if is_juv:
            score += 8
            factors.append("Age vulnerability: young pet (< 12 months) has elevated risk of rapid clinical decline")
            struct_factors.append(StructuredFactor(
                factor_name="Patient Age Vulnerability",
                finding="Young pet (< 12 months)",
                source=EvidenceSource.PATIENT_BASELINE.value,
                status=EvidenceStatus.PRESENT.value,
                direction=EvidenceDirection.RISK_INCREASING.value,
                rule_applied="Juvenile life-stage modifier (+8 pts)",
                rationale="Puppies and kittens have low physiological reserve and deteriorate quickly under illness.",
                contribution_pts=8,
            ))
        elif is_sen:
            score += 8
            factors.append("Age vulnerability: senior pet with increased susceptibility to complications")
            struct_factors.append(StructuredFactor(
                factor_name="Patient Age Vulnerability",
                finding="Senior pet",
                source=EvidenceSource.PATIENT_BASELINE.value,
                status=EvidenceStatus.PRESENT.value,
                direction=EvidenceDirection.RISK_INCREASING.value,
                rule_applied="Senior life-stage modifier (+8 pts)",
                rationale="Senior pets have higher incidence of co-morbidities and delayed recovery.",
                contribution_pts=8,
            ))

        if cond and str(cond).strip() and str(cond).strip().lower() not in ("none", "none reported", "n/a"):
            score += 6
            factors.append(f"Pre-existing health conditions in profile: {str(cond)[:60]}")
            struct_factors.append(StructuredFactor(
                factor_name="Pre-Existing Chronic Conditions",
                finding=str(cond).strip()[:80],
                source=EvidenceSource.PATIENT_BASELINE.value,
                status=EvidenceStatus.PRESENT.value,
                direction=EvidenceDirection.RISK_INCREASING.value,
                rule_applied="Chronic medical condition modifier (+6 pts)",
                rationale="Pre-existing illness predisposes patient to acute disease exacerbation.",
                contribution_pts=6,
            ))

        return min(15, score), factors, struct_factors

    def _calculate_image_score(
        self, evidence: NormalizedEvidence
    ) -> Tuple[int, List[str], List[StructuredFactor]]:
        """Calculate image score strictly adhering to CV safety rules.

        Safety & Integrity Rules:
        - Image existence alone never increases risk score.
        - Failed quality gates produce diagnostic notices, adding 0 pts.
        - Duplicate photos of the same lesion are only scored once.
        - If dermatological symptoms are already reported, erythema is treated as
          corroborating visual evidence (+2 pts) rather than compound additive risk (+5 pts).
        - Hard ceiling of 8 pts across all computer vision observations.
        """
        score = 0
        factors: List[str] = []
        struct_factors: List[StructuredFactor] = []

        # Check if patient already has active skin/dermatological symptoms reported
        has_skin_symptom = any(
            "skin" in str(sym.category).lower()
            or "skin" in str(sym.name).lower()
            or "red" in str(sym.name).lower()
            or "itch" in str(sym.name).lower()
            or "rash" in str(sym.name).lower()
            for sym in evidence.symptoms
        )

        erythema_awarded = False
        poor_quality_noted = False

        for img in evidence.image_observations:
            if img.id.endswith("_poor_quality"):
                if not poor_quality_noted:
                    poor_quality_noted = True
                    factors.append("Visual quality notice: attached photograph has insufficient lighting, focus, or resolution")
                    struct_factors.append(StructuredFactor(
                        factor_name="Computer Vision Quality Gate",
                        finding="Insufficient resolution, lighting, or focus",
                        source=EvidenceSource.IMAGE_CV.value,
                        status=EvidenceStatus.UNKNOWN.value,
                        direction=EvidenceDirection.UNKNOWN.value,
                        rule_applied="Image quality gate failed (0 pts added, uncertainty advisory issued)",
                        rationale="Sub-optimal photographic quality cannot confirm or exclude visual lesions.",
                        contribution_pts=0,
                    ))
            elif img.id.endswith("_erythema"):
                if not erythema_awarded:
                    erythema_awarded = True
                    sev = img.details.get("severity") or "moderate"

                    # Prevent duplicate attribution: if skin symptoms were already reported,
                    # treat image finding as corroborating rather than compound additive risk
                    if has_skin_symptom:
                        inc = 2  # Corroborating modifier
                        rule_desc = "Corroborating visual erythema (+2 pts, modulated to prevent double-counting with reported dermatological symptoms)"
                        rat_desc = "Objective visual erythema corroborates reported skin complaints without inflating total risk score through duplicate attribution."
                        factor_desc = "Corroborating visual observation: elevated localized erythema confirmed"
                    else:
                        inc = 5 if sev == "moderate" else 3
                        rule_desc = f"Independent visual erythema detection (+{inc} pts)"
                        rat_desc = "Objective superficial capillary engorgement consistent with localized irritation or inflammation."
                        factor_desc = "Computer vision observation: elevated localized erythema/redness observed"

                    score += inc
                    factors.append(factor_desc)
                    struct_factors.append(StructuredFactor(
                        factor_name="Visual Dermatological Inspection",
                        finding=img.display_value,
                        source=EvidenceSource.IMAGE_CV.value,
                        status=EvidenceStatus.PRESENT.value,
                        direction=EvidenceDirection.RISK_INCREASING.value,
                        rule_applied=rule_desc,
                        rationale=rat_desc,
                        contribution_pts=inc,
                    ))
                else:
                    # Additional image corroboration (0 additional points to prevent duplicate counting)
                    struct_factors.append(StructuredFactor(
                        factor_name="Secondary Visual Inspection",
                        finding=img.display_value,
                        source=EvidenceSource.IMAGE_CV.value,
                        status=EvidenceStatus.PRESENT.value,
                        direction=EvidenceDirection.RISK_INCREASING.value,
                        rule_applied="Additional photo corroboration (+0 pts to prevent duplicate scoring)",
                        rationale="Visual redness observed in secondary photo corroborates primary image finding without duplicating risk points.",
                        contribution_pts=0,
                    ))

        return min(8, score), factors, struct_factors

    def _generate_recommendation(self, risk_level: str, is_emergency: bool) -> str:
        """Generate compassionate, action-oriented, professional clinical recommendations."""
        if is_emergency or risk_level == "EMERGENCY":
            return (
                "IMMEDIATE EMERGENCY: Immediate veterinary medical attention is required. "
                "Transport your pet safely to the nearest 24/7 veterinary emergency hospital now."
            )
        if risk_level == "HIGH":
            return (
                "Urgent veterinary evaluation recommended as soon as possible (same day). "
                "Monitor pet closely and do not leave unattended."
            )
        if risk_level == "MODERATE":
            return (
                "Prompt veterinary examination recommended within 24–48 hours. "
                "Continue monitoring vital signs, appetite, and hydration."
            )
        return (
            "Routine monitoring recommended. Keep your pet comfortable and ensure clean water "
            "is available. Schedule a routine veterinary checkup if symptoms persist beyond 48 hours."
        )

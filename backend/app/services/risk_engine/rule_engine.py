"""Rule-based explainable health risk analysis engine.

Provides transparent clinical heuristic scoring based on pet baseline,
symptoms, duration, observations, follow-up answers, and emergency indicators.
"""
from typing import Dict, Any, List, Tuple
from app.services.risk_engine.base import BaseRiskAnalysisEngine, RiskAnalysisOutput
from app.services.emergency_service import EmergencyAssessmentService


class RuleBasedRiskAnalysisEngine(BaseRiskAnalysisEngine):
    """Clinical heuristic scoring engine with transparent explainability.

    This engine calculates a normalized 0–100 risk score and categorizes it into:
    - LOW (0–29)
    - MODERATE (30–59)
    - HIGH (60–84)
    - EMERGENCY (85–100 or hard-stop trigger)

    Emergency Hard-Stop Rule:
    Any acute critical indicator (e.g., severe dyspnea, seizure, severe pain,
    emergency follow-up response) immediately forces the risk level to EMERGENCY
    and enforces a floor score of 90, regardless of other low score components.
    """

    ENGINE_VERSION = "v1.0.0-rule_hybrid"

    # Base symptom severity points
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
        pet = payload.get("pet") or {}
        symptoms = payload.get("symptoms") or []
        observations = payload.get("observations") or {}
        answers = payload.get("follow_up_answers") or []

        key_factors: List[str] = []
        factor_breakdown: Dict[str, Any] = {}

        # 1. Emergency Screening Baseline (Step 2 & 3 integration)
        emergency_eval = EmergencyAssessmentService.evaluate_payload(payload)
        is_emergency = emergency_eval.get("is_emergency_flagged", False)
        emergency_flags = emergency_eval.get("flags", [])

        # 2. Symptom Severity Component (Max 55 pts)
        symptom_score, symptom_factors = self._calculate_symptom_score(symptoms)
        key_factors.extend(symptom_factors)
        factor_breakdown["symptom_score"] = symptom_score

        # 3. Symptom Duration Component (Max 18 pts)
        duration_score, duration_factors = self._calculate_duration_score(symptoms)
        key_factors.extend(duration_factors)
        factor_breakdown["duration_score"] = duration_score

        # 4. Physiological & Behavioral Observations (Max 30 pts)
        obs_score, obs_factors = self._calculate_observation_score(observations)
        key_factors.extend(obs_factors)
        factor_breakdown["observation_score"] = obs_score

        # 5. Dynamic Follow-Up Answers Component (Max 25 pts)
        answers_score, answer_factors = self._calculate_answers_score(answers)
        key_factors.extend(answer_factors)
        factor_breakdown["follow_up_score"] = answers_score

        # 6. Pet Vulnerability Modifiers (Age, Species, Chronic Conditions) (Max 15 pts)
        vuln_score, vuln_factors = self._calculate_vulnerability_score(pet)
        key_factors.extend(vuln_factors)
        factor_breakdown["vulnerability_modifier"] = vuln_score

        # 7. Computer Vision Visual Observations Component (Max 8 pts)
        img_analysis = payload.get("image_analysis") or {}
        img_score, img_factors = self._calculate_image_score(img_analysis)
        key_factors.extend(img_factors)
        factor_breakdown["image_score"] = img_score

        # 8. Aggregate Raw Score (Base Sum)
        raw_score = symptom_score + duration_score + obs_score + answers_score + vuln_score + img_score
        calculated_score = min(100, max(0, raw_score))
        factor_breakdown["raw_calculated_score"] = calculated_score

        # 9. Apply Emergency Hard-Stop Rule
        factor_breakdown["emergency_override"] = False

        if is_emergency or emergency_flags:
            is_emergency = True
            risk_level = "EMERGENCY"
            risk_score = max(calculated_score, 90)
            factor_breakdown["emergency_override"] = True
            # Place emergency flags prominently at the front of key factors
            emergency_descriptions = [f"CRITICAL: {flag}" for flag in emergency_flags]
            # Avoid duplicate factor notes
            key_factors = emergency_descriptions + [f for f in key_factors if f not in emergency_descriptions]
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

        # 9. Formulate Clear Action-Oriented Recommendation
        recommendation = self._generate_recommendation(risk_level, is_emergency)

        # 10. Clean and Deduplicate Factors (Top 6 most clinically relevant)
        seen_factors = set()
        deduped_factors = []
        for factor in key_factors:
            if factor and factor not in seen_factors:
                seen_factors.add(factor)
                deduped_factors.append(factor)

        if not deduped_factors:
            deduped_factors.append("Mild symptoms with stable physiological observations")

        return RiskAnalysisOutput(
            risk_level=risk_level,
            risk_score=risk_score,
            key_factors=deduped_factors[:6],
            factor_breakdown=factor_breakdown,
            recommendation=recommendation,
            is_emergency=is_emergency,
            engine_version=self.ENGINE_VERSION,
        )

    def _calculate_symptom_score(
        self, symptoms: List[Dict[str, Any]]
    ) -> Tuple[int, List[str]]:
        """Compute score contribution from reported symptoms."""
        if not symptoms:
            return 0, []

        factors: List[str] = []
        weights: List[int] = []

        for sym in symptoms:
            sev = (sym.get("severity") or "mild").lower()
            w = self.SEVERITY_WEIGHTS.get(sev, 12)
            weights.append(w)
            name = sym.get("name") or "Reported symptom"
            if sev == "severe":
                factors.append(f"Severe primary symptom: {name}")
            elif sev == "moderate":
                factors.append(f"Moderate symptom: {name}")

        weights.sort(reverse=True)
        primary_score = weights[0]
        # Diminishing weight for additional symptoms
        additional_score = sum(round(w * 0.4) for w in weights[1:])
        total_symptom_score = min(55, primary_score + min(20, additional_score))

        if len(symptoms) > 1:
            factors.append(f"Multiple co-occurring symptoms ({len(symptoms)} symptoms reported)")

        return total_symptom_score, factors

    def _calculate_duration_score(
        self, symptoms: List[Dict[str, Any]]
    ) -> Tuple[int, List[str]]:
        """Evaluate chronicity and progression risk from symptom duration."""
        if not symptoms:
            return 0, []

        max_hours = 0.0
        for sym in symptoms:
            dur_hours = sym.get("duration_hours")
            if dur_hours is not None and dur_hours > max_hours:
                max_hours = dur_hours

        factors: List[str] = []
        duration_score = 0

        if max_hours >= 168.0:  # > 7 days
            duration_score = 18
            factors.append("Symptoms persisting chronically for more than 1 week")
        elif max_hours >= 72.0:  # 3 to 7 days
            duration_score = 12
            factors.append("Symptoms persisting for several days (3–7 days)")
        elif max_hours >= 24.0:  # 1 to 3 days
            duration_score = 6
            factors.append("Symptoms persisting between 24 and 72 hours")
        elif max_hours > 0.0 and any((s.get("severity") or "").lower() in ("moderate", "severe") for s in symptoms):
            duration_score = 3
            factors.append("Acute symptom onset (< 24 hours)")

        return duration_score, factors

    def _calculate_observation_score(
        self, obs: Dict[str, Any]
    ) -> Tuple[int, List[str]]:
        """Score clinical observations for metabolic and physiological stability."""
        score = 0
        factors: List[str] = []

        # Appetite
        appetite = (obs.get("appetite") or "").lower()
        if appetite in ("none", "anorexia"):
            score += 14
            factors.append("Complete loss of appetite / anorexia")
        elif appetite == "decreased":
            score += 6
            factors.append("Decreased food intake observed")

        # Water intake
        water = (obs.get("water_intake") or "").lower()
        if water in ("none", "refusing"):
            score += 14
            factors.append("Refusal to drink water (acute dehydration risk)")
        elif water == "increased":
            score += 6
            factors.append("Polydipsia / significantly increased thirst")

        # Activity level
        activity = (obs.get("activity_level") or "").lower()
        if activity in ("depressed", "collapse"):
            score += 16
            factors.append("Marked depression or collapse in activity")
        elif activity == "lethargic":
            score += 10
            factors.append("Noticeable lethargy and sluggishness")
        elif activity == "decreased":
            score += 5

        # Respiration
        breathing = (obs.get("breathing_change") or "").lower()
        if breathing in ("labored", "wheezing"):
            score += 25
            factors.append("Abnormal respiratory effort: labored breathing / wheezing")
        elif breathing == "rapid":
            score += 12
            factors.append("Tachypnea / abnormally rapid breathing")

        # Pain
        pain = (obs.get("pain_observed") or "").lower()
        if pain == "severe":
            score += 22
            factors.append("Severe signs of physical pain or distress")
        elif pain == "moderate":
            score += 12
            factors.append("Moderate signs of pain or discomfort")
        elif pain == "mild":
            score += 5

        # Elimination (Stool / Urine)
        stool = (obs.get("stool_change") or "").lower()
        urine = (obs.get("urine_change") or "").lower()
        if any(term in stool for term in ("bloody", "black", "none", "watery")):
            score += 8
            factors.append(f"Abnormal stool changes noted: {stool}")
        if any(term in urine for term in ("bloody", "none", "straining", "frequent")):
            score += 10
            factors.append(f"Abnormal urinary pattern noted: {urine}")

        return min(30, score), factors

    def _calculate_answers_score(
        self, answers: List[Dict[str, Any]]
    ) -> Tuple[int, List[str]]:
        """Score responses from dynamic follow-up questions."""
        score = 0
        factors: List[str] = []

        for ans in answers:
            # Check weight
            weight = ans.get("severity_weight")
            if weight is not None and isinstance(weight, (int, float)):
                score += round(weight * 12)

            # Check textual hints of worsening or severity
            opt_val = (ans.get("answer_option_value") or "").lower()
            opt_text = (ans.get("answer_option") or "").lower()
            ans_text = (ans.get("answer_text") or "").lower()
            combined_text = f"{opt_val} {opt_text} {ans_text}"

            if any(term in combined_text for term in ("worsen", "worse", "increasing", "severe")):
                score += 5
                factors.append("Follow-up response indicates worsening clinical condition")
            elif any(term in combined_text for term in ("frequent", "persistent")):
                score += 3
                factors.append("Follow-up response confirms frequent or persistent recurrence")

        return min(25, score), factors

    def _calculate_vulnerability_score(
        self, pet: Dict[str, Any]
    ) -> Tuple[int, List[str]]:
        """Score physiological vulnerability based on age, species, and medical baseline."""
        score = 0
        factors: List[str] = []

        is_juvenile = pet.get("is_juvenile")
        is_senior = pet.get("is_senior")
        conditions = pet.get("existing_conditions")

        if is_juvenile:
            score += 8
            factors.append("Age vulnerability: young pet (< 12 months) has elevated risk of rapid clinical decline")
        elif is_senior:
            score += 8
            factors.append("Age vulnerability: senior pet with increased susceptibility to complications")

        if conditions:
            score += 6
            factors.append(f"Pre-existing health conditions in profile: {conditions[:60]}")

        return min(15, score), factors

    def _calculate_image_score(
        self, img_analysis: Dict[str, Any]
    ) -> Tuple[int, List[str]]:
        """Score structured observations extracted from computer vision image analysis.

        Crucial Safety Constraints:
        - Image existence alone never increases risk score.
        - Low quality images produce an informational notice, not disease conclusions.
        - Supported visual features (e.g. erythema) provide modest correlated signal (max 8 pts).
        """
        score = 0
        factors: List[str] = []

        observations = img_analysis.get("observations") or []
        for obs in observations:
            label = obs.get("observation_label", "")
            severity = (obs.get("severity") or "normal").lower()

            if label == "ELEVATED_ERYTHEMA_DETECTED":
                if severity == "moderate":
                    score += 5
                elif severity == "mild":
                    score += 3
                factors.append("Computer vision observation: elevated localized erythema/redness observed")
            elif label == "POOR_IMAGE_QUALITY":
                factors.append("Visual quality notice: attached photograph has insufficient lighting or resolution")

        return min(8, score), factors

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

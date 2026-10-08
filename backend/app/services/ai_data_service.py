from datetime import date
from typing import Dict, Any, List, Optional
from app.models.health_assessment import HealthAssessment


class AiDataPreparationService:
    """Transforms raw health assessments into a structured, validated AI-ready payload.
    
    This service prepares and standardizes health data for downstream AI inference
    (e.g., risk scoring, differential analysis, triage prioritization).
    It performs data preparation ONLY, without generating diagnoses.
    """

    @staticmethod
    def _normalize_duration_to_hours(val: Optional[float], unit: Optional[str]) -> Optional[float]:
        """Convert duration into standardized hours."""
        if val is None:
            return None
        unit_str = (unit or "").lower().strip()
        if "hour" in unit_str:
            return float(val)
        if "day" in unit_str:
            return float(val) * 24.0
        if "week" in unit_str:
            return float(val) * 168.0
        if "month" in unit_str:
            return float(val) * 720.0
        return float(val)

    @classmethod
    def prepare_ai_payload(cls, assessment: HealthAssessment) -> Dict[str, Any]:
        """Convert a HealthAssessment instance into a clean AI-ready dictionary."""
        pet = assessment.pet

        # Calculate age in months and developmental stage
        age_in_months: Optional[int] = None
        if pet and pet.date_of_birth:
            today = date.today()
            dob = pet.date_of_birth
            age_in_months = max(0, (today.year - dob.year) * 12 + (today.month - dob.month))
        elif pet and pet.age is not None:
            age_in_months = pet.age * 12

        is_juvenile = (age_in_months is not None and age_in_months < 12)
        is_senior = (pet.age is not None and pet.age >= 9) if pet else False

        # 1. Pet Demographic & Medical Baseline
        pet_profile: Dict[str, Any] = {
            "species": pet.species if pet else None,
            "breed": pet.breed if pet else None,
            "age": pet.age if pet else None,
            "age_in_months": age_in_months,
            "is_juvenile": is_juvenile,
            "is_senior": is_senior,
            "sex": pet.sex if pet else None,
            "weight": pet.weight if pet else None,
            "allergies": pet.allergies if pet else None,
            "existing_conditions": pet.existing_conditions if pet else None,
            "current_medications": pet.current_medications if pet else None,
        }

        # 2. Structured Symptoms with Severity & Duration
        symptoms_list: List[Dict[str, Any]] = []
        if assessment.symptoms:
            for item in assessment.symptoms:
                dur_hours = cls._normalize_duration_to_hours(
                    item.duration_value, item.duration_unit
                )
                symptoms_list.append({
                    "name": item.symptom.name if item.symptom else None,
                    "category": item.symptom.category if item.symptom else None,
                    "severity": item.severity,
                    "duration": {
                        "value": item.duration_value,
                        "unit": item.duration_unit,
                    },
                    "duration_hours": dur_hours,
                    "notes": item.notes,
                })

        # 3. Behavioral and Physiological Observations
        observations_data: Dict[str, Any] = {}
        if assessment.observations:
            obs = assessment.observations
            observations_data = {
                "appetite": obs.appetite,
                "water_intake": obs.water_intake,
                "activity_level": obs.activity_level,
                "behaviour_change": obs.behaviour_change,
                "sleep_change": obs.sleep_change,
                "stool_change": obs.stool_change,
                "urine_change": obs.urine_change,
                "breathing_change": obs.breathing_change,
                "pain_observed": obs.pain_observed,
            }
        else:
            observations_data = {
                "appetite": None,
                "water_intake": None,
                "activity_level": None,
                "behaviour_change": None,
                "sleep_change": None,
                "stool_change": None,
                "urine_change": None,
                "breathing_change": None,
                "pain_observed": None,
            }

        # 4. Aggregated Free-Text Notes
        combined_notes = ""
        if assessment.notes:
            combined_notes = "\n".join([n.note for n in assessment.notes if n.note])

        # 5. Step 3: Dynamic Follow-Up Question Answers
        #    Provides structured Q&A context to the downstream AI model.
        follow_up_answers: List[Dict[str, Any]] = []
        try:
            from app.models.assessment_answer import AssessmentAnswer
            answers = (
                AssessmentAnswer.query
                .filter_by(assessment_id=assessment.id)
                .order_by(AssessmentAnswer.created_at.asc())
                .all()
            )
            for ans in answers:
                q = ans.question
                follow_up_answers.append({
                    "question": q.question_text if q else None,
                    "category": q.category if q else None,
                    "priority": q.priority if q else None,
                    "is_emergency_related": q.is_emergency_related if q else False,
                    "question_type": q.question_type if q else None,
                    "answer_option": (
                        ans.selected_option.option_text if ans.selected_option else None
                    ),
                    "answer_option_value": (
                        ans.selected_option.option_value if ans.selected_option else None
                    ),
                    "answer_text": ans.answer_text,
                    "numeric_value": ans.numeric_value,
                    "boolean_value": ans.boolean_value,
                    "triggered_emergency": ans.triggered_emergency,
                    "severity_weight": (
                        ans.selected_option.severity_weight
                        if ans.selected_option else None
                    ),
                })
        except Exception:
            # Gracefully degrade if the answers table is unavailable
            follow_up_answers = []

        return {
            "pet": pet_profile,
            "symptoms": symptoms_list,
            "observations": observations_data,
            "additional_notes": combined_notes,
            "follow_up_answers": follow_up_answers,
        }

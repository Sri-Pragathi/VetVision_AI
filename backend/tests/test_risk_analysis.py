"""Tests for Step 4: AI Health Risk Analysis Engine.

Covers:
- Low-risk assessment evaluation
- Moderate-risk assessment evaluation
- High-risk assessment evaluation
- Emergency assessment evaluation (symptoms, observations, follow-up answers)
- Emergency hard-stop non-downgrade guarantee
- Duration progression risk effects
- Follow-up dynamic answers scoring impact
- Species / Age vulnerability modifiers
- Assessment state validation (no symptoms, cancelled)
- Multi-tenant security (401 unauthenticated, 403 forbidden)
- Idempotent re-running & record updating
- GET stored risk analysis retrieval
- Pluggable engine interface extensibility
"""
import pytest
from app.models.symptom import Symptom
from app.models.follow_up_question import FollowUpQuestion
from app.services.risk_engine import BaseRiskAnalysisEngine, RiskAnalysisOutput
from app.services.risk_analysis_service import RiskAnalysisService


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _get_symptom_id_by_name(client, name: str) -> str:
    """Helper to locate a seeded symptom ID by its exact or partial name."""
    res = client.get(f"/api/v1/symptoms?search={name}")
    data = res.get_json()["data"]
    for sym in data:
        if name.lower() in sym["name"].lower():
            return sym["id"]
    return data[0]["id"]


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_low_risk_assessment(client, registered_user, test_assessment):
    """1. Low-risk case: single mild symptom, normal observations, short duration."""
    sym_id = _get_symptom_id_by_name(client, "Sneezing")

    # Add mild symptom
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={
            "symptom_id": sym_id,
            "severity": "mild",
            "duration_value": 4,
            "duration_unit": "hours",
        },
    )

    # Normal observations
    client.put(
        f"/api/v1/assessments/{test_assessment['id']}/observations",
        headers=registered_user["headers"],
        json={
            "appetite": "normal",
            "activity_level": "normal",
            "water_intake": "normal",
        },
    )

    # Run Risk Analysis
    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    data = res.get_json()["data"]

    assert data["risk_level"] == "LOW"
    assert 0 <= data["risk_score"] < 30
    assert data["emergency"] is False
    assert data["is_emergency"] is False
    assert "Routine monitoring" in data["recommendation"]
    assert len(data["key_factors"]) >= 1
    assert "disclaimer" in data
    assert data["engine_version"] == "v1.0.0-rule_hybrid"


def test_moderate_risk_assessment(client, registered_user, test_assessment):
    """2. Moderate-risk case: moderate symptom with decreased appetite and 2-day duration."""
    sym_id = _get_symptom_id_by_name(client, "Vomiting")

    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={
            "symptom_id": sym_id,
            "severity": "moderate",
            "duration_value": 2,
            "duration_unit": "days",
        },
    )

    client.put(
        f"/api/v1/assessments/{test_assessment['id']}/observations",
        headers=registered_user["headers"],
        json={
            "appetite": "decreased",
            "activity_level": "decreased",
        },
    )

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    data = res.get_json()["data"]

    assert data["risk_level"] == "MODERATE"
    assert 30 <= data["risk_score"] < 60
    assert data["emergency"] is False
    assert "24–48 hours" in data["recommendation"]


def test_high_risk_assessment(client, registered_user, test_assessment):
    """3. High-risk case: severe symptom persisting > 3 days with lethargy and anorexia."""
    sym_id = _get_symptom_id_by_name(client, "Diarrhea")

    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={
            "symptom_id": sym_id,
            "severity": "severe",
            "duration_value": 4,
            "duration_unit": "days",
        },
    )

    client.put(
        f"/api/v1/assessments/{test_assessment['id']}/observations",
        headers=registered_user["headers"],
        json={
            "appetite": "none",
            "activity_level": "lethargic",
            "water_intake": "none",
        },
    )

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    data = res.get_json()["data"]

    assert data["risk_level"] in ("HIGH", "EMERGENCY")
    assert data["risk_score"] >= 60
    assert "Urgent" in data["recommendation"] or "EMERGENCY" in data["recommendation"]


def test_emergency_via_critical_symptom(client, registered_user, test_assessment):
    """4. Emergency trigger via critical symptom (Difficulty Breathing)."""
    sym_id = _get_symptom_id_by_name(client, "Difficulty Breathing")

    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={
            "symptom_id": sym_id,
            "severity": "severe",
            "duration_value": 1,
            "duration_unit": "hours",
        },
    )

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    data = res.get_json()["data"]

    assert data["risk_level"] == "EMERGENCY"
    assert data["risk_score"] >= 90
    assert data["emergency"] is True
    assert data["is_emergency"] is True
    assert "IMMEDIATE EMERGENCY" in data["recommendation"]
    assert any("difficulty breathing" in f.lower() for f in data["key_factors"])


def test_emergency_via_labored_breathing_observation(client, registered_user, test_assessment):
    """5. Emergency trigger via labored respiration in observations."""
    sym_id = _get_symptom_id_by_name(client, "Coughing")

    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={
            "symptom_id": sym_id,
            "severity": "mild",
            "duration_value": 2,
            "duration_unit": "hours",
        },
    )

    # Observation with labored breathing
    client.put(
        f"/api/v1/assessments/{test_assessment['id']}/observations",
        headers=registered_user["headers"],
        json={
            "breathing_change": "labored",
        },
    )

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    data = res.get_json()["data"]

    assert data["risk_level"] == "EMERGENCY"
    assert data["risk_score"] >= 90
    assert data["emergency"] is True
    assert any("respiration" in f.lower() or "breathing" in f.lower() for f in data["key_factors"])


def test_emergency_via_severe_pain_observation(client, registered_user, test_assessment):
    """6. Emergency trigger via severe pain in observations."""
    sym_id = _get_symptom_id_by_name(client, "Limping")

    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={
            "symptom_id": sym_id,
            "severity": "mild",
            "duration_value": 1,
            "duration_unit": "days",
        },
    )

    client.put(
        f"/api/v1/assessments/{test_assessment['id']}/observations",
        headers=registered_user["headers"],
        json={
            "pain_observed": "severe",
        },
    )

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    data = res.get_json()["data"]

    assert data["risk_level"] == "EMERGENCY"
    assert data["risk_score"] >= 90
    assert data["emergency"] is True


def test_emergency_via_follow_up_answer(client, registered_user, test_assessment):
    """7. Emergency trigger via dynamic follow-up answer option flagged as emergency."""
    sym_id = _get_symptom_id_by_name(client, "Vomiting")

    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={
            "symptom_id": sym_id,
            "severity": "mild",
            "duration_value": 2,
            "duration_unit": "hours",
        },
    )

    # Get dynamic questions
    q_res = client.get(
        f"/api/v1/assessments/{test_assessment['id']}/next-questions?batch_size=5",
        headers=registered_user["headers"],
    )
    questions = q_res.get_json()["data"]["questions"]
    assert len(questions) > 0

    # Pick an option that has emergency_flag == True, or answer with emergency
    target_q = None
    target_opt = None
    for q in questions:
        for opt in q.get("options", []):
            if opt.get("emergency_flag"):
                target_q = q
                target_opt = opt
                break
        if target_q:
            break

    # If none in first batch, find one directly from DB for test
    if not target_q:
        db_q = FollowUpQuestion.query.filter_by(is_emergency_related=True).first()
        target_q = db_q.to_dict(include_options=True)
        target_opt = [o for o in target_q["options"] if o.get("emergency_flag")][0]

    # Submit the emergency answer
    ans_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/answers",
        headers=registered_user["headers"],
        json={
            "question_id": target_q["id"],
            "selected_option_id": target_opt["id"],
        },
    )
    assert ans_res.status_code == 201

    # Run analysis
    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    data = res.get_json()["data"]

    assert data["risk_level"] == "EMERGENCY"
    assert data["risk_score"] >= 90
    assert data["emergency"] is True
    assert data["factor_breakdown"]["emergency_override"] is True


def test_emergency_hard_stop_never_downgraded(client, registered_user, test_assessment):
    """8. Emergency conditions are NEVER downgraded even if other factors are minimal."""
    sym_id = _get_symptom_id_by_name(client, "Seizures")

    # Single moderate symptom, minimal duration, normal observations
    sym_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={
            "symptom_id": sym_id,
            "severity": "moderate",
            "duration_value": 1,
            "duration_unit": "hours",
        },
    )
    assert sym_res.status_code == 201

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )
    data = res.get_json()["data"]

    # Even though only 1 symptom and 10 mins, seizure is acute emergency
    assert data["risk_level"] == "EMERGENCY"
    assert data["risk_score"] >= 90
    assert data["emergency"] is True


def test_duration_progressing_risk(client, registered_user, test_pet):
    """9. Chronic or progressing duration increases risk score and adds duration factor."""
    # Create two separate assessments to compare durations
    res1 = client.post(f"/api/v1/pets/{test_pet['id']}/assessments", headers=registered_user["headers"])
    asmt_short = res1.get_json()["data"]["id"]

    res2 = client.post(f"/api/v1/pets/{test_pet['id']}/assessments", headers=registered_user["headers"])
    asmt_long = res2.get_json()["data"]["id"]

    sym_id = _get_symptom_id_by_name(client, "Coughing")

    # Short duration (1 day)
    client.post(
        f"/api/v1/assessments/{asmt_short}/symptoms",
        headers=registered_user["headers"],
        json={"symptom_id": sym_id, "severity": "mild", "duration_value": 1, "duration_unit": "days"},
    )

    # Long duration (2 weeks)
    client.post(
        f"/api/v1/assessments/{asmt_long}/symptoms",
        headers=registered_user["headers"],
        json={"symptom_id": sym_id, "severity": "mild", "duration_value": 2, "duration_unit": "weeks"},
    )

    out_short = client.post(f"/api/v1/assessments/{asmt_short}/risk-analysis", headers=registered_user["headers"]).get_json()["data"]
    out_long = client.post(f"/api/v1/assessments/{asmt_long}/risk-analysis", headers=registered_user["headers"]).get_json()["data"]

    assert out_long["risk_score"] > out_short["risk_score"]
    assert any("week" in f.lower() or "chronic" in f.lower() for f in out_long["key_factors"])


def test_follow_up_answers_influence_score(client, registered_user, test_assessment):
    """10. Answers indicating high severity or worsening symptoms increase score."""
    sym_id = _get_symptom_id_by_name(client, "Diarrhea")

    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={"symptom_id": sym_id, "severity": "moderate", "duration_value": 2, "duration_unit": "days"},
    )

    base_analysis = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    ).get_json()["data"]

    # Submit an answer with high severity_weight
    q = FollowUpQuestion.query.filter_by(category="Digestive").first()
    # Find option with highest severity weight
    options = sorted(q.options, key=lambda o: o.severity_weight or 0, reverse=True)
    high_opt = options[0]

    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/answers",
        headers=registered_user["headers"],
        json={
            "question_id": q.id,
            "selected_option_id": high_opt.id,
            "answer_text": "Symptoms are worsening rapidly",
        },
    )

    updated_analysis = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    ).get_json()["data"]

    assert updated_analysis["risk_score"] >= base_analysis["risk_score"]
    assert updated_analysis["factor_breakdown"]["follow_up_score"] > 0


def test_pet_vulnerability_juvenile_and_senior(client, registered_user):
    """11. Juvenile or senior pets receive vulnerability modifiers."""
    # Create young puppy (3 months old)
    puppy_res = client.post(
        "/api/v1/pets",
        headers=registered_user["headers"],
        json={
            "name": "Tiny",
            "species": "Canine",
            "date_of_birth": "2026-07-01",  # ~3 months old
            "existing_conditions": "Congenital murmur",
        },
    )
    puppy = puppy_res.get_json()["data"]

    asmt_res = client.post(f"/api/v1/pets/{puppy['id']}/assessments", headers=registered_user["headers"])
    puppy_asmt = asmt_res.get_json()["data"]

    sym_id = _get_symptom_id_by_name(client, "Lethargy")
    client.post(
        f"/api/v1/assessments/{puppy_asmt['id']}/symptoms",
        headers=registered_user["headers"],
        json={"symptom_id": sym_id, "severity": "moderate", "duration_value": 1, "duration_unit": "days"},
    )

    analysis = client.post(
        f"/api/v1/assessments/{puppy_asmt['id']}/risk-analysis",
        headers=registered_user["headers"],
    ).get_json()["data"]

    assert analysis["factor_breakdown"]["vulnerability_modifier"] > 0
    assert any("vulnerability" in f.lower() or "conditions" in f.lower() for f in analysis["key_factors"])


def test_cannot_analyze_assessment_without_symptoms(client, registered_user, test_assessment):
    """12. Validates error when attempting to analyze assessment without symptoms."""
    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )
    assert res.status_code == 422
    data = res.get_json()
    assert "symptom" in data["message"].lower()


def test_cannot_analyze_cancelled_assessment(client, registered_user, test_assessment):
    """13. Validates error when attempting to analyze a cancelled assessment."""
    sym_id = _get_symptom_id_by_name(client, "Vomiting")
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={"symptom_id": sym_id, "severity": "mild", "duration_value": 1, "duration_unit": "days"},
    )

    # Cancel assessment
    client.put(
        f"/api/v1/assessments/{test_assessment['id']}",
        headers=registered_user["headers"],
        json={"status": "cancelled"},
    )

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )
    assert res.status_code == 422
    data = res.get_json()
    assert "cancelled" in data["message"].lower()


def test_unauthorized_and_forbidden_risk_analysis(client, registered_user, second_user, test_assessment):
    """14. Validates 401 unauthenticated and 403 forbidden security."""
    sym_id = _get_symptom_id_by_name(client, "Coughing")
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={"symptom_id": sym_id, "severity": "mild", "duration_value": 1, "duration_unit": "days"},
    )

    # Missing token -> 401
    unauth = client.post(f"/api/v1/assessments/{test_assessment['id']}/risk-analysis")
    assert unauth.status_code == 401

    # Second user accessing first user's assessment -> 403
    forbidden = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=second_user["headers"],
    )
    assert forbidden.status_code == 403


def test_idempotent_rerun_updates_stored_analysis(client, registered_user, test_assessment):
    """15. Re-running risk analysis updates existing record without creating duplicate."""
    sym_id = _get_symptom_id_by_name(client, "Sneezing")
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={"symptom_id": sym_id, "severity": "mild", "duration_value": 2, "duration_unit": "hours"},
    )

    # First run
    res1 = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )
    assert res1.status_code == 200
    first_data = res1.get_json()["data"]
    first_id = first_data["id"]

    # Now add more severe symptoms
    sym2_id = _get_symptom_id_by_name(client, "Difficulty Breathing")
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={"symptom_id": sym2_id, "severity": "severe", "duration_value": 1, "duration_unit": "hours"},
    )

    # Second run
    res2 = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )
    assert res2.status_code == 200
    second_data = res2.get_json()["data"]

    # Same record ID updated in place
    assert second_data["id"] == first_id
    assert second_data["risk_level"] == "EMERGENCY"
    assert second_data["risk_score"] > first_data["risk_score"]


def test_get_stored_risk_analysis(client, registered_user, test_assessment):
    """16. GET returns stored analysis; GET before running returns 404."""
    # Before running analysis -> 404
    get_before = client.get(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )
    assert get_before.status_code == 404

    # Add symptom and run analysis
    sym_id = _get_symptom_id_by_name(client, "Itching")
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={"symptom_id": sym_id, "severity": "moderate", "duration_value": 3, "duration_unit": "days"},
    )
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )

    # GET after running analysis -> 200
    get_after = client.get(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )
    assert get_after.status_code == 200
    data = get_after.get_json()["data"]
    assert data["assessment_id"] == test_assessment["id"]
    assert "risk_score" in data
    assert "key_factors" in data
    assert "recommendation" in data
    assert "disclaimer" in data


def test_pluggable_engine_extensibility(client, registered_user, test_assessment):
    """17. Verifies BaseRiskAnalysisEngine adapter architecture can be replaced cleanly."""
    class CustomMockMLEngine(BaseRiskAnalysisEngine):
        @property
        def version(self) -> str:
            return "v2.0.0-mock_ml_model"

        def analyze(self, payload):
            return RiskAnalysisOutput(
                risk_level="HIGH",
                risk_score=75,
                key_factors=["ML Model identified high disease probability"],
                factor_breakdown={"model_confidence": 0.85},
                recommendation="ML Recommendation: Consult veterinarian.",
                is_emergency=False,
                engine_version=self.version,
            )

    sym_id = _get_symptom_id_by_name(client, "Vomiting")
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={"symptom_id": sym_id, "severity": "mild", "duration_value": 1, "duration_unit": "days"},
    )

    # Execute with custom engine
    result = RiskAnalysisService.analyze_assessment(
        assessment_id=test_assessment["id"],
        user_id=registered_user["user"]["id"],
        engine=CustomMockMLEngine(),
    )

    assert result["engine_version"] == "v2.0.0-mock_ml_model"
    assert result["risk_score"] == 75
    assert result["risk_level"] == "HIGH"
    assert "ML Model" in result["key_factors"][0]

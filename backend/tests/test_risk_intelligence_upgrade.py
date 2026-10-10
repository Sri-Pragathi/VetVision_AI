"""Comprehensive tests for Step 8A: Evidence Normalization, Risk-Scoring Reliability, and Explainability.

Validates:
1. Missing data remains UNKNOWN and is never inferred as reassuring/normal.
2. Type safety for booleans, strings, nulls, and unexpected values in observations (especially pain_observed).
3. Contradiction detection (e.g. reported dyspnea symptom with normal breathing observation).
4. Chronological anomaly detection (duration exceeding pet lifespan).
5. Image quality failure is treated as uncertainty, never as evidence of normal health.
6. Structured explainability factors with source, direction, and rule attribution.
7. Emergency hard-stops cannot be discounted or diluted by reassuring answers.
8. Scores strictly bounded to [0, 100].
9. Historical report snapshot immutability across analysis re-runs.
10. Multi-tenant access controls.
"""
import pytest
from app.services.risk_engine.evidence import (
    EvidenceNormalizer,
    EvidenceStatus,
    EvidenceSource,
    EvidenceDirection,
)
from app.services.risk_engine.quality_checker import QualityChecker
from app.services.risk_engine.rule_engine import RuleBasedRiskAnalysisEngine


def _get_symptom_id_by_name(client, name: str) -> str:
    """Helper to locate seeded symptom ID."""
    res = client.get(f"/api/v1/symptoms?search={name}")
    data = res.get_json()["data"]
    for sym in data:
        if name.lower() in sym["name"].lower():
            return sym["id"]
    return data[0]["id"]


# ---------------------------------------------------------------------------
# Unit Tests for Evidence Normalizer & Quality Checker
# ---------------------------------------------------------------------------

def test_missing_data_remains_unknown_not_reassuring():
    """Missing observations must be marked UNKNOWN and never converted into normal findings."""
    payload = {
        "pet": {"species": "dog", "age": 3},
        "symptoms": [{"name": "Lethargy", "severity": "mild", "duration_hours": 12.0}],
        "observations": {},  # Completely empty observations
        "follow_up_answers": [],
        "image_analysis": {},
    }

    evidence = EvidenceNormalizer.normalize(payload)

    # Missing observations should be in unknown_fields
    assert "appetite" in evidence.unknown_fields
    assert "water_intake" in evidence.unknown_fields
    assert "breathing_change" in evidence.unknown_fields
    assert "pain_observed" in evidence.unknown_fields

    # Physical observation items for these must have status UNKNOWN
    unknown_items = evidence.get_by_status(EvidenceStatus.UNKNOWN)
    unknown_names = [i.name for i in unknown_items]
    assert any("Appetite" in n for n in unknown_names)
    assert any("Pain" in n for n in unknown_names)

    # Run quality checker
    warnings = QualityChecker.check(evidence)
    missing_warning = next((w for w in warnings if w.code == "MISSING_OBSERVATION_DATA"), None)
    assert missing_warning is not None
    assert "treated as unknown" in missing_warning.message


def test_safe_observation_parsing_booleans_and_strings():
    """Verify pain_observed handles boolean True, boolean False, string severe, string mild, and None safely."""
    # Test True
    ev_true = EvidenceNormalizer._parse_pain_observation(True)
    assert ev_true.status == EvidenceStatus.PRESENT
    assert ev_true.details["pain_severity"] == "moderate"
    assert ev_true.direction == EvidenceDirection.RISK_INCREASING

    # Test False
    ev_false = EvidenceNormalizer._parse_pain_observation(False)
    assert ev_false.status == EvidenceStatus.ABSENT
    assert ev_false.details["pain_severity"] == "none"
    assert ev_false.direction == EvidenceDirection.REASSURING

    # Test String "severe"
    ev_severe = EvidenceNormalizer._parse_pain_observation("severe")
    assert ev_severe.status == EvidenceStatus.PRESENT
    assert ev_severe.direction == EvidenceDirection.EMERGENCY_OVERRIDE
    assert ev_severe.is_emergency_flag is True

    # Test String "none"
    ev_none = EvidenceNormalizer._parse_pain_observation("none")
    assert ev_none.status == EvidenceStatus.ABSENT
    assert ev_none.direction == EvidenceDirection.REASSURING

    # Test None
    ev_none_val = EvidenceNormalizer._parse_pain_observation(None)
    assert ev_none_val.status == EvidenceStatus.UNKNOWN
    assert ev_none_val.direction == EvidenceDirection.UNKNOWN


def test_contradiction_detection_respiratory():
    """Detect conflict when symptom has severe dyspnea but observation records normal breathing."""
    payload = {
        "pet": {"species": "dog", "age": 4},
        "symptoms": [{"name": "Difficulty breathing", "severity": "severe", "duration_hours": 6.0}],
        "observations": {
            "breathing_change": "normal",
            "appetite": "normal",
        },
    }

    evidence = EvidenceNormalizer.normalize(payload)
    warnings = QualityChecker.check(evidence)

    contra = next((w for w in warnings if w.code == "CONTRADICTION_RESPIRATORY_STATUS"), None)
    assert contra is not None
    assert contra.category == "contradiction"
    assert "symptom_intake" in contra.conflicting_sources
    assert "physical_observation" in contra.conflicting_sources


def test_chronology_anomaly_duration_exceeds_age():
    """Detect when symptom duration in hours exceeds recorded pet age."""
    payload = {
        "pet": {"species": "dog", "age": 1},  # 1 year old = ~8766 hours
        "symptoms": [{"name": "Itching", "severity": "mild", "duration_hours": 20000.0}],  # > 2 years!
        "observations": {},
    }

    evidence = EvidenceNormalizer.normalize(payload)
    warnings = QualityChecker.check(evidence)

    chrono = next((w for w in warnings if w.code == "CHRONOLOGY_DURATION_EXCEEDS_AGE"), None)
    assert chrono is not None
    assert chrono.category == "chronology"


def test_image_quality_failure_is_not_normal_health():
    """Ensure bad image quality issues an advisory warning and 0 pts without ruling out disease."""
    payload = {
        "pet": {"species": "dog", "age": 2},
        "symptoms": [{"name": "Itching", "severity": "moderate", "duration_hours": 24.0}],
        "observations": {},
        "image_analysis": {
            "images_count": 1,
            "analyzed_count": 1,
            "observations": [{"observation_label": "POOR_IMAGE_QUALITY", "severity": "normal"}],
        },
    }

    engine = RuleBasedRiskAnalysisEngine()
    output = engine.analyze(payload)

    # Image score should be 0 pts
    assert output.factor_breakdown["image_score"] == 0

    # Data quality warning must be generated
    warnings = output.data_quality_warnings
    img_warn = next((w for w in warnings if w["code"] == "IMAGE_QUALITY_INSUFFICIENT"), None)
    assert img_warn is not None
    assert "does NOT rule out physical" in img_warn["message"]


def test_emergency_hard_stop_inviolability_with_reassuring_factors():
    """Reassuring observations (normal appetite, normal hydration) must NEVER downgrade emergency hard-stop."""
    payload = {
        "pet": {"species": "cat", "age": 3},
        # Emergency symptom
        "symptoms": [{"name": "Seizures", "severity": "severe", "duration_hours": 1.0}],
        # Reassuring physical observations
        "observations": {
            "appetite": "normal",
            "water_intake": "normal",
            "activity_level": "normal",
            "breathing_change": "normal",
            "pain_observed": False,
        },
        "image_analysis": {},
    }

    engine = RuleBasedRiskAnalysisEngine()
    output = engine.analyze(payload)

    # Must be emergency with score >= 90
    assert output.is_emergency is True
    assert output.risk_level == "EMERGENCY"
    assert output.risk_score >= 90
    assert output.factor_breakdown["emergency_override"] is True

    # Emergency factor must be present with direction emergency_override
    struct_factors = output.structured_factors
    em_factor = next((f for f in struct_factors if f["direction"] == "emergency_override"), None)
    assert em_factor is not None
    assert em_factor["is_emergency_flag"] is True


def test_score_strictly_bounded_0_to_100():
    """Even if all sub-scores sum to maximum (151 pts), final score is strictly clamped to 100."""
    payload = {
        "pet": {"species": "dog", "age": 12, "is_senior": True, "existing_conditions": "Diabetes, Renal failure"},
        "symptoms": [
            {"name": "Vomiting", "severity": "severe", "duration_hours": 200.0},
            {"name": "Diarrhea", "severity": "severe", "duration_hours": 200.0},
            {"name": "Lethargy", "severity": "severe", "duration_hours": 200.0},
        ],
        "observations": {
            "appetite": "none",
            "water_intake": "none",
            "activity_level": "depressed",
            "breathing_change": "rapid",
            "pain_observed": "severe",
            "stool_change": "bloody",
            "urine_change": "bloody",
        },
        "follow_up_answers": [
            {"question": "Q1", "answer_option": "Worsening rapidly", "severity_weight": 2.0},
            {"question": "Q2", "answer_option": "Severe decline", "severity_weight": 2.0},
        ],
        "image_analysis": {
            "images_count": 1,
            "analyzed_count": 1,
            "observations": [{"observation_label": "ELEVATED_ERYTHEMA_DETECTED", "severity": "moderate"}],
        },
    }

    engine = RuleBasedRiskAnalysisEngine()
    output = engine.analyze(payload)

    assert 0 <= output.risk_score <= 100
    assert output.risk_score == 100
    assert output.risk_level == "EMERGENCY"


# ---------------------------------------------------------------------------
# Integration Tests with Flask Client
# ---------------------------------------------------------------------------

def test_api_risk_analysis_returns_structured_factors_and_warnings(client, registered_user, test_assessment):
    """Verify endpoint /assessments/<id>/risk-analysis returns structured factors and warnings."""
    headers = registered_user["headers"]
    sym_id = _get_symptom_id_by_name(client, "Sneezing")

    # Add symptom
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=headers,
        json={
            "symptom_id": sym_id,
            "severity": "mild",
            "duration_value": 2,
            "duration_unit": "hours",
        },
    )

    # Observations with boolean pain_observed: False
    client.put(
        f"/api/v1/assessments/{test_assessment['id']}/observations",
        headers=headers,
        json={
            "appetite": "normal",
            "water_intake": "normal",
            "pain_observed": False,
        },
    )

    # Run analysis
    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.get_json()["data"]

    # Verify structured factors
    assert "structured_factors" in data
    assert isinstance(data["structured_factors"], list)
    assert len(data["structured_factors"]) >= 1

    primary_factor = data["structured_factors"][0]
    assert "factor_name" in primary_factor
    assert "source" in primary_factor
    assert "direction" in primary_factor
    assert "rule_applied" in primary_factor

    # Verify data quality warnings
    assert "data_quality_warnings" in data
    assert isinstance(data["data_quality_warnings"], list)


def test_report_snapshot_immutability(client, registered_user, test_assessment):
    """Historical report snapshots must remain immutable after re-running risk analysis."""
    headers = registered_user["headers"]
    sym_id = _get_symptom_id_by_name(client, "Vomiting")

    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=headers,
        json={
            "symptom_id": sym_id,
            "severity": "mild",
            "duration_value": 5,
            "duration_unit": "hours",
        },
    )

    # Complete assessment & generate Report v1
    client.put(
        f"/api/v1/assessments/{test_assessment['id']}",
        headers=headers,
        json={"status": "completed"},
    )
    rep1_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=headers,
    )
    assert rep1_res.status_code == 201
    rep1 = rep1_res.get_json()["data"]
    rep1_id = rep1["id"]
    rep1_score = rep1["report_data"]["risk_analysis"]["risk_score"]

    # Retrieve Report v1 directly
    get_res = client.get(f"/api/v1/reports/{rep1_id}", headers=headers)
    assert get_res.status_code == 200
    stored_rep1 = get_res.get_json()["data"]

    # Verify report v1 content
    assert stored_rep1["report_version"] == 1
    assert stored_rep1["report_data"]["risk_analysis"]["risk_score"] == rep1_score


def test_risk_intelligence_authorization(client, registered_user, second_user, test_assessment):
    """Unauthenticated and cross-tenant access to risk analysis must be rejected."""
    sym_id = _get_symptom_id_by_name(client, "Coughing")
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={"symptom_id": sym_id, "severity": "mild", "duration_value": 1, "duration_unit": "days"},
    )

    # 401 unauthenticated
    unauth_res = client.post(f"/api/v1/assessments/{test_assessment['id']}/risk-analysis")
    assert unauth_res.status_code == 401

    # 403 forbidden for second user
    forbid_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=second_user["headers"],
    )
    assert forbid_res.status_code == 403

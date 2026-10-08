"""Comprehensive tests for Step 6: Veterinary Report & Explainable Health Summary.

Test Scenarios Covered:
1. Report generation for valid completed assessment
2. Report contains complete Pet Profile (without fabrication)
3. Report contains Reported Symptoms (names, category, severity, duration)
4. Report contains Dynamic Follow-up Findings & Answers
5. Report contains Clinical Observations (appetite, hydration, mobility, etc.)
6. Report contains Image Analysis findings with cautious non-diagnostic language
7. Report contains Step 4 Risk Analysis (score, level, factor breakdown)
8. Report contains Explainability section (why the risk level was assigned)
9. Report contains Emergency Indicators (normal state vs urgent state)
10. Report contains Recommended Next Action from risk engine
11. Report contains Veterinary Handoff Summary
12. Report contains Safety Disclaimer
13. Missing optional data is handled safely (graceful fallback, no crash)
14. Image not provided scenario handled cleanly ("No images uploaded")
15. Image uploaded but analysis not completed handled cleanly ("Analysis pending")
16. Image quality failure handled cleanly ("insufficient for reliable visual analysis")
17. Multi-tenant ownership/security (authenticated user can only access their own reports)
18. Unauthorized access blocked (401 Missing JWT)
19. Forbidden access blocked (403 User B cannot access User A's report)
20. Report versioning: snapshots are immutable, re-generation creates new version
21. Report listing endpoint returns historical versions ordered descending
22. HTML rendering produces clean, semantic, structured HTML report
23. HTML escaping / XSS injection safety (user notes and pet names are sanitized)
24. Emergency assessment hard-stop remains clearly represented in reports
"""
import io
import pytest
from PIL import Image, ImageDraw
from app.models.symptom import Symptom
from app.models.follow_up_question import FollowUpQuestion
from app.models.assessment_report import AssessmentReport
from app.services.report_service import ReportService
from app.services.report_html_renderer import ReportHtmlRenderer


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

def _get_symptom_id_by_name(client, name: str) -> str:
    """Helper to locate seeded symptom ID by name."""
    res = client.get(f"/api/v1/symptoms?search={name}")
    data = res.get_json()["data"]
    for sym in data:
        if name.lower() in sym["name"].lower():
            return sym["id"]
    return data[0]["id"]


def _create_test_image(
    width: int = 300,
    height: int = 300,
    color: tuple = (180, 140, 100),
) -> io.BytesIO:
    """Generate in-memory valid PIL test image."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width // 2, height], fill=(70, 50, 30))
    draw.rectangle([width // 4, height // 4, 3 * width // 4, 3 * height // 4], fill=(220, 180, 140))
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def _create_dark_test_image(width: int = 300, height: int = 300) -> io.BytesIO:
    """Generate dark / underexposed image for quality gate failure."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=(10, 10, 10))
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def _populate_full_assessment(client, registered_user, test_assessment):
    """Populate an assessment with symptoms, observations, follow-ups, and image analysis."""
    assessment_id = test_assessment["id"]
    headers = registered_user["headers"]

    # 1. Add Symptoms (Coughing, Lethargy)
    cough_id = _get_symptom_id_by_name(client, "Coughing")
    client.post(
        f"/api/v1/assessments/{assessment_id}/symptoms",
        headers=headers,
        json={
            "symptom_id": cough_id,
            "severity": "moderate",
            "duration_value": 3,
            "duration_unit": "days",
            "notes": "Dry hacking cough especially after exercise",
        },
    )

    lethargy_id = _get_symptom_id_by_name(client, "Lethargy")
    client.post(
        f"/api/v1/assessments/{assessment_id}/symptoms",
        headers=headers,
        json={
            "symptom_id": lethargy_id,
            "severity": "mild",
            "duration_value": 2,
            "duration_unit": "days",
            "notes": "Reluctant to go on regular walks",
        },
    )

    # 2. Add Clinical Observations
    client.put(
        f"/api/v1/assessments/{assessment_id}/observations",
        headers=headers,
        json={
            "appetite": "decreased",
            "water_intake": "normal",
            "activity_level": "lethargic",
            "behaviour_change": "withdrawn",
            "sleep_change": "sleeping_more",
        },
    )

    # 3. Add Clinical Note
    client.post(
        f"/api/v1/assessments/{assessment_id}/notes",
        headers=headers,
        json={"note": "Owner noted symptoms began after boarding over the weekend."},
    )

    # 4. Answer Dynamic Follow-up Questions
    q_res = client.get(
        f"/api/v1/assessments/{assessment_id}/next-questions",
        headers=headers,
    )
    if q_res.status_code == 200:
        questions = q_res.get_json()["data"].get("questions", [])
        if questions:
            q = questions[0]
            answer_payload = {
                "question_id": q["id"],
                "answer_text": "Coughing episodes happen roughly twice a day.",
            }
            if q.get("options"):
                answer_payload["selected_option_id"] = q["options"][0]["id"]
            client.post(
                f"/api/v1/assessments/{assessment_id}/answers",
                headers=headers,
                json=answer_payload,
            )

    # 5. Upload and analyze an image
    img_buf = _create_test_image()
    up_res = client.post(
        f"/api/v1/assessments/{assessment_id}/images",
        headers=headers,
        data={
            "image": (img_buf, "chest_area.jpg"),
            "image_type": "symptom_area",
            "body_part": "chest",
            "caption": "Photo of pet resting",
        },
        content_type="multipart/form-data",
    )
    img_data = up_res.get_json()["data"]
    client.post(
        f"/api/v1/assessment-images/{img_data['id']}/analyze",
        headers=headers,
    )

    # 6. Mark assessment completed
    client.put(
        f"/api/v1/assessments/{assessment_id}",
        headers=headers,
        json={"status": "completed"},
    )


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_generate_report_valid_completed_assessment(client, registered_user, test_assessment):
    """Test 1: Report generation succeeds for a completed assessment with status 201."""
    _populate_full_assessment(client, registered_user, test_assessment)

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    assert res.status_code == 201
    body = res.get_json()
    assert body["success"] is True
    report = body["data"]

    assert report["assessment_id"] == test_assessment["id"]
    assert report["report_version"] == 1
    assert report["report_status"] == "GENERATED"
    assert "report_data" in report
    assert "disclaimer" in report


def test_report_contains_all_13_sections(client, registered_user, test_assessment):
    """Test 2: Generated report data payload contains all 13 required structured sections."""
    _populate_full_assessment(client, registered_user, test_assessment)

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    data = res.get_json()["data"]["report_data"]

    required_sections = [
        "metadata",
        "pet",
        "assessment",
        "symptoms",
        "follow_up_findings",
        "observations",
        "image_analysis",
        "risk_analysis",
        "explainability",
        "emergency",
        "recommendation",
        "veterinary_handoff",
        "disclaimer",
    ]
    for section in required_sections:
        assert section in data, f"Missing section '{section}' in report_data"


def test_report_pet_profile(client, registered_user, test_assessment, test_pet):
    """Test 3: Pet profile in report contains accurate information without fabrication."""
    _populate_full_assessment(client, registered_user, test_assessment)

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    pet = res.get_json()["data"]["report_data"]["pet"]

    assert pet["id"] == test_pet["id"]
    assert pet["name"] == test_pet["name"]
    assert pet["species"] == test_pet["species"]
    assert pet["breed"] == test_pet["breed"]
    assert pet["sex"] == test_pet["sex"]
    assert pet["weight"] == test_pet["weight"]
    assert pet["allergies"] == test_pet["allergies"]
    assert pet["existing_conditions"] == test_pet["existing_conditions"]
    assert pet["current_medications"] == test_pet["current_medications"]
    assert pet["vaccination_status"] == test_pet["vaccination_status"]


def test_report_symptoms_content(client, registered_user, test_assessment):
    """Test 4: Symptoms section contains names, categories, severity, duration, and notes."""
    _populate_full_assessment(client, registered_user, test_assessment)

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    symptoms = res.get_json()["data"]["report_data"]["symptoms"]

    assert len(symptoms) >= 2
    symptom_names_lower = [s["name"].lower() for s in symptoms]
    assert "coughing" in symptom_names_lower
    assert "lethargy" in symptom_names_lower

    cough = next(s for s in symptoms if s["name"].lower() == "coughing")
    assert cough["severity"] == "moderate"
    assert cough["duration"] == "3 days"
    assert cough["notes"] == "Dry hacking cough especially after exercise"


def test_report_follow_up_findings(client, registered_user, test_assessment):
    """Test 5: Follow-up section captures dynamic Q&A in human-readable structure."""
    _populate_full_assessment(client, registered_user, test_assessment)

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    findings = res.get_json()["data"]["report_data"]["follow_up_findings"]

    assert len(findings) >= 1
    f = findings[0]
    assert "question" in f
    assert "answer" in f
    assert "selected_option" in f


def test_report_clinical_observations(client, registered_user, test_assessment):
    """Test 6: Observations section correctly records appetite, energy, and notes."""
    _populate_full_assessment(client, registered_user, test_assessment)

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    obs = res.get_json()["data"]["report_data"]["observations"]

    assert obs["appetite"] == "decreased"
    assert obs["activity_level"] == "lethargic"
    assert obs["water_intake"] == "normal"
    assert obs["behaviour_change"] == "withdrawn"
    assert obs["sleep_change"] == "sleeping_more"


def test_report_image_analysis_findings(client, registered_user, test_assessment):
    """Test 7: Image analysis findings describe visual observations without diagnostic certainty."""
    _populate_full_assessment(client, registered_user, test_assessment)

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    images = res.get_json()["data"]["report_data"]["image_analysis"]

    assert len(images) == 1
    img = images[0]
    assert img["status"] == "COMPLETED"
    assert "quality" in img
    assert img["quality"]["check_passed"] is True
    assert "visual_observations" in img
    assert "detected_visual_features" in img
    # Cautious non-diagnostic wording check
    assert "definitive diagnosis" not in str(img).lower()


def test_report_risk_analysis_and_explainability(client, registered_user, test_assessment):
    """Test 8: Preserves Step 4 risk analysis and provides explainable factor breakdown."""
    _populate_full_assessment(client, registered_user, test_assessment)

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    data = res.get_json()["data"]["report_data"]
    risk = data["risk_analysis"]
    explainability = data["explainability"]

    assert "risk_level" in risk
    assert "risk_score" in risk
    assert "key_factors" in risk
    assert "factor_breakdown" in risk
    assert "engine_version" in risk

    assert len(explainability) > 0
    for factor in explainability:
        assert "factor" in factor
        assert "finding" in factor
        assert "relevance" in factor
        assert "explanation" in factor


def test_report_emergency_indicators_normal(client, registered_user, test_assessment):
    """Test 9: Low assessments reflect clear non-emergency status."""
    headers = registered_user["headers"]
    sym_id = _get_symptom_id_by_name(client, "Sneezing")
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=headers,
        json={"symptom_id": sym_id, "severity": "mild", "duration_value": 2, "duration_unit": "hours"},
    )
    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=headers,
    )
    assert res.status_code == 201
    emergency = res.get_json()["data"]["report_data"]["emergency"]

    assert emergency["is_emergency"] is False
    assert emergency["status"] == "No emergency indicators identified"
    assert len(emergency["emergency_triggers"]) == 0


def test_report_emergency_indicators_triggered(client, registered_user, test_assessment):
    """Test 10: Critical symptom triggers emergency status with clear urgent evaluation notice."""
    headers = registered_user["headers"]
    assessment_id = test_assessment["id"]

    # Add emergency symptom: Difficulty Breathing with severe severity
    dyspnea_id = _get_symptom_id_by_name(client, "Difficulty Breathing")
    client.post(
        f"/api/v1/assessments/{assessment_id}/symptoms",
        headers=headers,
        json={
            "symptom_id": dyspnea_id,
            "severity": "severe",
            "duration_value": 1,
            "duration_unit": "hours",
            "notes": "Labored open-mouth breathing with blue gums",
        },
    )

    res = client.post(
        f"/api/v1/assessments/{assessment_id}/reports",
        headers=headers,
    )
    assert res.status_code == 201
    emergency = res.get_json()["data"]["report_data"]["emergency"]

    assert emergency["is_emergency"] is True
    assert emergency["status"] == "Emergency veterinary attention recommended"
    assert len(emergency["emergency_triggers"]) > 0


def test_report_recommendations(client, registered_user, test_assessment):
    """Test 11: Report includes clear action recommendation without prescribing medication."""
    _populate_full_assessment(client, registered_user, test_assessment)

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    rec = res.get_json()["data"]["report_data"]["recommendation"]

    assert "primary_action" in rec
    assert "urgency_level" in rec
    assert "guidance" in rec
    # Must not prescribe drugs or dosage
    guidance = rec["guidance"].lower()
    assert "mg" not in guidance
    assert "prescribe" not in guidance


def test_report_veterinary_handoff_summary(client, registered_user, test_assessment):
    """Test 12: Handoff summary provides concise clinical brief for veterinary team."""
    _populate_full_assessment(client, registered_user, test_assessment)

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    handoff = res.get_json()["data"]["report_data"]["veterinary_handoff"]

    assert "pet_summary" in handoff
    assert "primary_reported_concerns" in handoff
    assert "reported_symptoms" in handoff
    assert "clinical_observations_summary" in handoff
    assert "risk_level" in handoff
    assert "emergency_status" in handoff
    assert "recommended_next_action" in handoff


def test_report_safety_disclaimer(client, registered_user, test_assessment):
    """Test 13: Report prominently features veterinary legal and safety disclaimer."""
    _populate_full_assessment(client, registered_user, test_assessment)

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    body = res.get_json()["data"]

    assert "definitive veterinary diagnosis" in body["disclaimer"]
    assert "qualified veterinarian" in body["disclaimer"]
    assert body["report_data"]["disclaimer"] == body["disclaimer"]


def test_report_image_not_provided(client, registered_user, test_assessment):
    """Test 14: Handles assessment without image upload cleanly."""
    headers = registered_user["headers"]
    sym_id = _get_symptom_id_by_name(client, "Sneezing")
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=headers,
        json={"symptom_id": sym_id, "severity": "mild", "duration_value": 1, "duration_unit": "days"},
    )

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=headers,
    )
    assert res.status_code == 201
    images = res.get_json()["data"]["report_data"]["image_analysis"]

    assert len(images) == 1
    assert images[0]["status"] == "NOT_PROVIDED"
    assert "No image provided" in images[0]["visual_observations"]


def test_report_image_analysis_not_completed(client, registered_user, test_assessment):
    """Test 15: Image uploaded but analysis not run is represented as pending."""
    headers = registered_user["headers"]
    sym_id = _get_symptom_id_by_name(client, "Sneezing")
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=headers,
        json={"symptom_id": sym_id, "severity": "mild", "duration_value": 1, "duration_unit": "days"},
    )
    # Upload image without calling /analyze
    img_buf = _create_test_image()
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=headers,
        data={"image": (img_buf, "test.jpg"), "image_type": "symptom_area"},
        content_type="multipart/form-data",
    )

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=headers,
    )
    assert res.status_code == 201
    images = res.get_json()["data"]["report_data"]["image_analysis"]

    assert len(images) == 1
    assert images[0]["status"] == "PENDING"
    assert "Analysis not completed" in images[0]["visual_observations"]


def test_report_image_quality_failure(client, registered_user, test_assessment):
    """Test 16: Image with failed quality check is identified clearly as insufficient quality."""
    headers = registered_user["headers"]
    sym_id = _get_symptom_id_by_name(client, "Sneezing")
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=headers,
        json={"symptom_id": sym_id, "severity": "mild", "duration_value": 1, "duration_unit": "days"},
    )
    # Upload dark image and analyze
    dark_buf = _create_dark_test_image()
    up_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=headers,
        data={"image": (dark_buf, "dark.jpg"), "image_type": "symptom_area"},
        content_type="multipart/form-data",
    )
    img_id = up_res.get_json()["data"]["id"]
    client.post(
        f"/api/v1/assessment-images/{img_id}/analyze",
        headers=headers,
    )

    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=headers,
    )
    assert res.status_code == 201
    images = res.get_json()["data"]["report_data"]["image_analysis"]

    assert len(images) == 1
    assert images[0]["status"] == "REQUIRES_BETTER_IMAGE"
    assert "insufficient for reliable visual analysis" in images[0]["visual_observations"]


def test_report_versioning_and_regeneration(client, registered_user, test_assessment):
    """Test 17 & 18: Regenerating report creates new immutable version (v1 -> v2) and archives previous."""
    _populate_full_assessment(client, registered_user, test_assessment)

    # 1. Generate version 1
    res1 = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    rep1 = res1.get_json()["data"]
    assert rep1["report_version"] == 1
    assert rep1["report_status"] == "GENERATED"
    rep1_id = rep1["id"]

    # 2. Add an additional symptom to assessment
    vomit_id = _get_symptom_id_by_name(client, "Vomiting")
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={"symptom_id": vomit_id, "severity": "severe", "duration_value": 1, "duration_unit": "days"},
    )

    # 3. Generate version 2
    res2 = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    rep2 = res2.get_json()["data"]
    assert rep2["report_version"] == 2
    assert rep2["report_status"] == "GENERATED"
    assert rep2["id"] != rep1_id

    # 4. Fetch version 1 by ID: check immutability (does NOT contain Vomiting, marked ARCHIVED)
    res_get_v1 = client.get(
        f"/api/v1/reports/{rep1_id}",
        headers=registered_user["headers"],
    )
    v1_data = res_get_v1.get_json()["data"]
    assert v1_data["report_version"] == 1
    assert v1_data["report_status"] == "ARCHIVED"
    v1_sym_names = [s["name"].lower() for s in v1_data["report_data"]["symptoms"]]
    assert "vomiting" not in v1_sym_names

    # 5. Fetch version 2: contains Vomiting
    v2_sym_names = [s["name"].lower() for s in rep2["report_data"]["symptoms"]]
    assert "vomiting" in v2_sym_names


def test_report_listing_endpoint(client, registered_user, test_assessment):
    """Test 19: List reports returns all versions ordered descending."""
    _populate_full_assessment(client, registered_user, test_assessment)

    # Generate v1 and v2
    client.post(f"/api/v1/assessments/{test_assessment['id']}/reports", headers=registered_user["headers"])
    client.post(f"/api/v1/assessments/{test_assessment['id']}/reports", headers=registered_user["headers"])

    res = client.get(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    reports = res.get_json()["data"]
    assert len(reports) == 2
    assert reports[0]["report_version"] == 2
    assert reports[1]["report_version"] == 1


def test_report_html_rendering_endpoint(client, registered_user, test_assessment):
    """Test 20: GET /reports/<id>/html returns valid HTML document with styling and content."""
    _populate_full_assessment(client, registered_user, test_assessment)

    gen_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    report_id = gen_res.get_json()["data"]["id"]

    html_res = client.get(
        f"/api/v1/reports/{report_id}/html",
        headers=registered_user["headers"],
    )
    assert html_res.status_code == 200
    assert "text/html" in html_res.content_type
    html_text = html_res.get_data(as_text=True)

    assert "<!DOCTYPE html>" in html_text
    assert "VETVISION AI" in html_text
    assert "Veterinary Health Assessment Report" in html_text
    assert "Max" in html_text
    assert "Coughing" in html_text
    assert "Safety Disclaimer" in html_text


def test_report_content_negotiation_html(client, registered_user, test_assessment):
    """Test 21: GET /reports/<id> with Accept: text/html serves HTML."""
    _populate_full_assessment(client, registered_user, test_assessment)

    gen_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    report_id = gen_res.get_json()["data"]["id"]

    headers = dict(registered_user["headers"])
    headers["Accept"] = "text/html"

    res = client.get(
        f"/api/v1/reports/{report_id}",
        headers=headers,
    )
    assert res.status_code == 200
    assert "text/html" in res.content_type
    assert "<!DOCTYPE html>" in res.get_data(as_text=True)


def test_html_escaping_and_xss_safety(client, registered_user, test_assessment):
    """Test 22: HTML rendering escapes malicious input (prevents XSS injection)."""
    headers = registered_user["headers"]
    sym_id = _get_symptom_id_by_name(client, "Sneezing")
    xss_payload = "<script>alert('xss')</script><img src=x onerror=alert(1)>"

    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=headers,
        json={
            "symptom_id": sym_id,
            "severity": "mild",
            "duration_value": 1,
            "duration_unit": "days",
            "notes": xss_payload,
        },
    )

    gen_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=headers,
    )
    report_id = gen_res.get_json()["data"]["id"]

    html_res = client.get(
        f"/api/v1/reports/{report_id}/html",
        headers=headers,
    )
    html_text = html_res.get_data(as_text=True)

    # Must NOT contain raw unescaped script tags
    assert "<script>alert('xss')</script>" not in html_text
    assert "<img src=x onerror=alert(1)>" not in html_text
    # Must contain escaped versions
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in html_text or "&lt;script&gt;" in html_text


def test_report_multi_tenant_security(client, registered_user, second_user, test_assessment):
    """Test 23: Multi-tenant authorization (401 unauthenticated, 403 forbidden)."""
    _populate_full_assessment(client, registered_user, test_assessment)

    # 1. Unauthenticated request to generate report -> 401
    res = client.post(f"/api/v1/assessments/{test_assessment['id']}/reports")
    assert res.status_code == 401

    # Generate report as owner
    gen_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=registered_user["headers"],
    )
    report_id = gen_res.get_json()["data"]["id"]

    # 2. Second user attempts to generate report on User 1's assessment -> 403
    res_gen_sec = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/reports",
        headers=second_user["headers"],
    )
    assert res_gen_sec.status_code == 403

    # 3. Second user attempts to view User 1's report -> 403
    res_get_sec = client.get(
        f"/api/v1/reports/{report_id}",
        headers=second_user["headers"],
    )
    assert res_get_sec.status_code == 403

    # 4. Second user attempts to view User 1's HTML report -> 403
    res_html_sec = client.get(
        f"/api/v1/reports/{report_id}/html",
        headers=second_user["headers"],
    )
    assert res_html_sec.status_code == 403

    # 5. Nonexistent report -> 404
    res_404 = client.get(
        "/api/v1/reports/00000000-0000-0000-0000-000000000000",
        headers=registered_user["headers"],
    )
    assert res_404.status_code == 404


def test_report_validation_errors(client, registered_user, test_assessment):
    """Test 24: Rejects report generation for cancelled assessments or empty symptoms."""
    headers = registered_user["headers"]
    assessment_id = test_assessment["id"]

    # 1. Assessment without symptoms -> 400 or 422
    res_empty = client.post(
        f"/api/v1/assessments/{assessment_id}/reports",
        headers=headers,
    )
    assert res_empty.status_code in [400, 422]
    assert "at least one reported symptom" in res_empty.get_json()["message"]

    # Add symptom, then cancel assessment
    sym_id = _get_symptom_id_by_name(client, "Sneezing")
    client.post(
        f"/api/v1/assessments/{assessment_id}/symptoms",
        headers=headers,
        json={"symptom_id": sym_id, "severity": "mild", "duration_value": 1, "duration_unit": "days"},
    )
    client.put(
        f"/api/v1/assessments/{assessment_id}",
        headers=headers,
        json={"status": "cancelled"},
    )

    # 2. Cancelled assessment -> 400 or 422
    res_cancelled = client.post(
        f"/api/v1/assessments/{assessment_id}/reports",
        headers=headers,
    )
    assert res_cancelled.status_code in [400, 422]
    assert "cancelled" in res_cancelled.get_json()["message"]

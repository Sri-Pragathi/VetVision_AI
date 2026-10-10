"""Complete End-to-End User Journey & Security Integration Test Suite for Step 8C.

Validates the full 16-step user journey:
1. Application online check (/api/v1/health)
2. User registration (/api/v1/auth/register)
3. User login (/api/v1/auth/login)
4. Pet profile creation (/api/v1/pets)
5. Assessment initiation (/api/v1/pets/<pet_id>/assessments)
6. Symptom selection (/api/v1/assessments/<id>/symptoms)
7. Dynamic follow-up questions & answer submission (/api/v1/assessments/<id>/next-questions & /answers)
8. Clinical physical observations recording (/api/v1/assessments/<id>/observations)
9. Pet photograph upload (/api/v1/assessments/<id>/images)
10. Computer-vision quality gate & visual analysis (/api/v1/assessment-images/<img_id>/analyze)
11. AI health risk analysis execution (/api/v1/assessments/<id>/risk-analysis)
12. Verification of risk score, structured explainability factors, and warnings
13. Veterinary report generation (/api/v1/assessments/<id>/reports)
14. Report verification across all 13 clinical sections (/api/v1/reports/<report_id>)
15. Veterinary handoff summary copy & print-friendly HTML rendering (/api/v1/reports/<report_id>/html)
16. Logout and token revocation enforcement (/api/v1/auth/logout)

Also validates negative edge cases, multi-tenant isolation, lifecycle guards, and production security.
"""
import io
import pytest
from PIL import Image, ImageDraw
from app import create_app
from app.models.symptom import Symptom
from app.models.follow_up_question import FollowUpQuestion


def _create_valid_test_image() -> io.BytesIO:
    """Generate in-memory valid test image meeting all CV quality thresholds."""
    buf = io.BytesIO()
    img = Image.new("RGB", (320, 320), color=(175, 140, 105))
    draw = ImageDraw.Draw(img)
    draw.rectangle([60, 60, 260, 260], fill=(70, 45, 25), outline=(0, 0, 0))
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def _get_symptom_id(client, name: str) -> str:
    """Helper to query seeded symptoms through standard API."""
    res = client.get("/api/v1/symptoms")
    assert res.status_code == 200
    for sym in res.get_json()["data"]:
        if name.lower() in sym["name"].lower():
            return sym["id"]
    raise ValueError(f"Symptom '{name}' not found in vocabulary")


def test_complete_16_step_happy_path_user_journey(client):
    """Verify the entire end-to-end happy path user journey across all 16 milestones."""

    # -------------------------------------------------------------------------
    # STEP 1: Open the Application / Check Health
    # -------------------------------------------------------------------------
    health_res = client.get("/api/v1/health")
    assert health_res.status_code == 200
    assert health_res.get_json()["success"] is True
    assert health_res.get_json()["message"] == "VetVision AI backend is running"

    # -------------------------------------------------------------------------
    # STEP 2: Register a New User
    # -------------------------------------------------------------------------
    user_payload = {
        "name": "Dr. Sarah Jenkins",
        "email": "sarah.jenkins@vetvision.ai",
        "password": "SecurePassword123!",
    }
    reg_res = client.post("/api/v1/auth/register", json=user_payload)
    assert reg_res.status_code == 201
    user_data = reg_res.get_json()["data"]["user"]
    assert user_data["email"] == "sarah.jenkins@vetvision.ai"

    # -------------------------------------------------------------------------
    # STEP 3: Log in and Obtain Authenticated Session Tokens
    # -------------------------------------------------------------------------
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    assert login_res.status_code == 200
    tokens = login_res.get_json()["data"]["tokens"]
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # -------------------------------------------------------------------------
    # STEP 4: Create a Pet Profile
    # -------------------------------------------------------------------------
    pet_payload = {
        "name": "Bella",
        "species": "Dog",
        "breed": "Golden Retriever",
        "sex": "female",
        "weight": 28.5,
        "allergies": "Seasonal pollen",
        "existing_conditions": "None reported",
    }
    pet_res = client.post("/api/v1/pets", headers=headers, json=pet_payload)
    assert pet_res.status_code == 201
    pet_id = pet_res.get_json()["data"]["id"]
    assert pet_res.get_json()["data"]["name"] == "Bella"

    # -------------------------------------------------------------------------
    # STEP 5: Open that Pet's Health Assessment
    # -------------------------------------------------------------------------
    start_res = client.post(f"/api/v1/pets/{pet_id}/assessments", headers=headers)
    assert start_res.status_code == 201
    assessment_id = start_res.get_json()["data"]["id"]
    assert start_res.get_json()["data"]["status"] == "in_progress"

    # -------------------------------------------------------------------------
    # STEP 6: Select Symptoms
    # -------------------------------------------------------------------------
    cough_sym_id = _get_symptom_id(client, "Cough")

    sym_payload = {
        "symptom_id": cough_sym_id,
        "severity": "moderate",
        "duration_value": 2,
        "duration_unit": "days",
        "notes": "Dry hacking cough after light exercise",
    }
    sym_res = client.post(
        f"/api/v1/assessments/{assessment_id}/symptoms",
        headers=headers,
        json=sym_payload,
    )
    assert sym_res.status_code == 201

    # -------------------------------------------------------------------------
    # STEP 7: Answer Applicable Dynamic Follow-Up Questions
    # -------------------------------------------------------------------------
    q_res = client.get(
        f"/api/v1/assessments/{assessment_id}/next-questions",
        headers=headers,
    )
    assert q_res.status_code == 200
    questions = q_res.get_json()["data"]["questions"]
    assert len(questions) > 0, "Dynamic question engine must serve questions for reported cough"

    target_q = questions[0]
    ans_payload = {"question_id": target_q["id"]}
    if target_q["question_type"] == "yes_no":
        ans_payload["boolean_value"] = False
    elif target_q["question_type"] == "single_choice" and target_q.get("options"):
        ans_payload["selected_option_id"] = target_q["options"][0]["id"]
    else:
        ans_payload["boolean_value"] = False

    ans_res = client.post(
        f"/api/v1/assessments/{assessment_id}/answers",
        headers=headers,
        json=ans_payload,
    )
    assert ans_res.status_code == 201

    # -------------------------------------------------------------------------
    # STEP 8: Enter Observations Where Supported
    # -------------------------------------------------------------------------
    obs_payload = {
        "appetite": "normal",
        "activity_level": "normal",
        "breathing_change": "normal",
        "pain_observed": "none",
        "water_intake": "normal",
    }
    obs_res = client.put(
        f"/api/v1/assessments/{assessment_id}/observations",
        headers=headers,
        json=obs_payload,
    )
    assert obs_res.status_code == 200

    # -------------------------------------------------------------------------
    # STEP 9: Upload a Valid Pet Image
    # -------------------------------------------------------------------------
    img_bytes = _create_valid_test_image()
    up_res = client.post(
        f"/api/v1/assessments/{assessment_id}/images",
        headers=headers,
        data={"image": (img_bytes, "bella_inspection.jpg"), "image_type": "symptom_area"},
        content_type="multipart/form-data",
    )
    assert up_res.status_code == 201
    img_id = up_res.get_json()["data"]["id"]

    # -------------------------------------------------------------------------
    # STEP 10: Verify Image-Quality Feedback and Analysis Behavior
    # -------------------------------------------------------------------------
    cv_res = client.post(
        f"/api/v1/assessment-images/{img_id}/analyze",
        headers=headers,
    )
    assert cv_res.status_code == 200
    cv_data = cv_res.get_json()["data"]
    assert cv_data["quality_gate"] == "PASSED"
    assert cv_data["analysis_status"] in ["ANALYZED", "COMPLETED"]
    assert "quality_metrics" in cv_data
    assert cv_data["quality_metrics"]["is_sharp"] is True
    assert cv_data["quality_metrics"]["is_well_lit"] is True
    assert len(cv_data["actionable_guidance"]) == 0

    # -------------------------------------------------------------------------
    # STEP 11: Run AI Health Risk Analysis
    # -------------------------------------------------------------------------
    risk_res = client.post(
        f"/api/v1/assessments/{assessment_id}/risk-analysis",
        headers=headers,
    )
    assert risk_res.status_code == 200
    risk_data = risk_res.get_json()["data"]

    # -------------------------------------------------------------------------
    # STEP 12: Inspect Risk Level, Score, Evidence, Structured Factors, & Warnings
    # -------------------------------------------------------------------------
    assert risk_data["risk_level"] in ["LOW", "MODERATE", "HIGH", "EMERGENCY"]
    assert 0 <= risk_data["risk_score"] <= 100
    assert len(risk_data["key_factors"]) > 0
    assert "factor_breakdown" in risk_data
    assert "structured_factors" in risk_data
    assert len(risk_data["structured_factors"]) > 0
    # Confirm factor attribution traceability
    primary_factor = risk_data["structured_factors"][0]
    assert "factor_name" in primary_factor
    assert "source" in primary_factor
    assert "rule_applied" in primary_factor
    assert "direction" in primary_factor

    # -------------------------------------------------------------------------
    # STEP 13: Generate a Veterinary Report
    # -------------------------------------------------------------------------
    rep_gen_res = client.post(
        f"/api/v1/assessments/{assessment_id}/reports",
        headers=headers,
    )
    assert rep_gen_res.status_code == 201
    report_id = rep_gen_res.get_json()["data"]["id"]
    assert rep_gen_res.get_json()["data"]["report_version"] == 1

    # -------------------------------------------------------------------------
    # STEP 14: Open the Report and Verify All Sections Render Correctly
    # -------------------------------------------------------------------------
    rep_res = client.get(f"/api/v1/reports/{report_id}", headers=headers)
    assert rep_res.status_code == 200
    rep_body = rep_res.get_json()["data"]["report_data"]

    # Verify all 13 clinical report snapshot sections
    expected_sections = [
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
    for section in expected_sections:
        assert section in rep_body, f"Expected section '{section}' missing from report snapshot"

    assert rep_body["pet"]["name"] == "Bella"
    assert len(rep_body["symptoms"]) == 1
    assert rep_body["image_analysis"][0]["status"] == "COMPLETED"
    assert "definitive veterinary diagnosis" in rep_body["disclaimer"]

    # -------------------------------------------------------------------------
    # STEP 15: Copy Veterinary Handoff Summary & Use Print-Friendly HTML View
    # -------------------------------------------------------------------------
    handoff = rep_body["veterinary_handoff"]
    assert "pet_summary" in handoff
    assert "Bella" in handoff["pet_summary"]
    assert "recommended_next_action" in handoff

    html_res = client.get(f"/api/v1/reports/{report_id}/html", headers=headers)
    assert html_res.status_code == 200
    assert "text/html" in html_res.content_type
    html_content = html_res.get_data(as_text=True)
    assert "Veterinary Health Assessment Report" in html_content
    assert "Bella" in html_content
    assert "Golden Retriever" in html_content
    assert "@media print" in html_content  # Print-friendly stylesheet

    # -------------------------------------------------------------------------
    # STEP 16: Log Out and Verify Protected Endpoints Require Authentication
    # -------------------------------------------------------------------------
    logout_res = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200

    # Verify that the revoked token can no longer access protected endpoints
    guarded_res = client.get("/api/v1/pets", headers=headers)
    assert guarded_res.status_code == 401
    assert "token has been revoked" in guarded_res.get_json()["message"].lower() or guarded_res.status_code == 401


def test_negative_security_and_lifecycle_edge_cases(client, registered_user, second_user, test_assessment):
    """Verify security isolation, emergency retention, and lifecycle constraints."""
    user1_headers = registered_user["headers"]
    user2_headers = second_user["headers"]
    assessment_id = test_assessment["id"]

    # 1. Invalid Login Credentials Rejected
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@vetvision.ai", "password": "WrongPassword123!"},
    )
    assert bad_login.status_code == 401

    # 2. Accessing Protected Resources Without Authentication Rejected
    unauth_res = client.get("/api/v1/pets")
    assert unauth_res.status_code == 401

    # 3. Multi-Tenant Authorization Protection (User 2 accessing User 1's assessment)
    user2_attempt = client.get(
        f"/api/v1/assessments/{assessment_id}/images",
        headers=user2_headers,
    )
    assert user2_attempt.status_code == 403

    # 4. Lifecycle Constraint: Cancelled Assessment Rejects Image Uploads
    client.put(
        f"/api/v1/assessments/{assessment_id}",
        headers=user1_headers,
        json={"status": "cancelled"},
    )
    img_bytes = _create_valid_test_image()
    cancel_up = client.post(
        f"/api/v1/assessments/{assessment_id}/images",
        headers=user1_headers,
        data={"image": (img_bytes, "test.jpg")},
        content_type="multipart/form-data",
    )
    assert cancel_up.status_code in [400, 422]

    # 5. Unsupported Upload Format Rejected
    text_buf = io.BytesIO(b"Not an image")
    bad_up = client.post(
        f"/api/v1/assessments/{assessment_id}/images",
        headers=user1_headers,
        data={"image": (text_buf, "malicious.exe")},
        content_type="multipart/form-data",
    )
    assert bad_up.status_code in [400, 422]

    # 6. Production Security Guard: Refuses boot if default fallback secrets are used
    with pytest.raises(ValueError, match="SECURITY CONFIGURATION ERROR"):
        create_app("production")


def test_emergency_override_retention_with_reassuring_image(client, registered_user, test_assessment):
    """Verify that a reassuring photograph cannot reduce risk or cancel emergency triage."""
    headers = registered_user["headers"]
    assessment_id = test_assessment["id"]

    # 1. Add emergency symptom: Difficulty Breathing (severe)
    dyspnea_id = _get_symptom_id(client, "Breathing")
    client.post(
        f"/api/v1/assessments/{assessment_id}/symptoms",
        headers=headers,
        json={
            "symptom_id": dyspnea_id,
            "severity": "severe",
            "duration_value": 1,
            "duration_unit": "hours",
            "notes": "Severe respiratory distress",
        },
    )

    # 2. Add normal/reassuring image
    img_bytes = _create_valid_test_image()
    up_res = client.post(
        f"/api/v1/assessments/{assessment_id}/images",
        headers=headers,
        data={"image": (img_bytes, "reassuring.jpg")},
        content_type="multipart/form-data",
    )
    img_id = up_res.get_json()["data"]["id"]
    client.post(f"/api/v1/assessment-images/{img_id}/analyze", headers=headers)

    # 3. Execute risk analysis
    risk_res = client.post(
        f"/api/v1/assessments/{assessment_id}/risk-analysis",
        headers=headers,
    )
    assert risk_res.status_code == 200
    risk_data = risk_res.get_json()["data"]

    # EMERGENCY invariants: Floor >= 90, level EMERGENCY, override True
    assert risk_data["is_emergency"] is True
    assert risk_data["risk_level"] == "EMERGENCY"
    assert risk_data["risk_score"] >= 90
    assert risk_data["factor_breakdown"]["emergency_override"] is True
    assert "IMMEDIATE EMERGENCY" in risk_data["recommendation"]


def test_contradiction_detection_warning_and_missing_data_unknown(client, registered_user, test_assessment):
    """Verify that contradictory findings trigger clinical warnings and missing fields remain UNKNOWN."""
    headers = registered_user["headers"]
    assessment_id = test_assessment["id"]

    # 1. Add severe respiratory symptom
    dyspnea_id = _get_symptom_id(client, "Breathing")
    client.post(
        f"/api/v1/assessments/{assessment_id}/symptoms",
        headers=headers,
        json={
            "symptom_id": dyspnea_id,
            "severity": "severe",
            "duration_value": 2,
            "duration_unit": "hours",
        },
    )

    # 2. Add contradictory observation: normal breathing recorded by owner
    client.put(
        f"/api/v1/assessments/{assessment_id}/observations",
        headers=headers,
        json={"breathing_change": "normal", "activity_level": "normal"},
    )

    # 3. Run risk analysis without image
    risk_res = client.post(
        f"/api/v1/assessments/{assessment_id}/risk-analysis",
        headers=headers,
    )
    assert risk_res.status_code == 200
    risk_data = risk_res.get_json()["data"]

    # Warnings must contain contradiction warning
    warnings = risk_data.get("data_quality_warnings", [])
    assert any(w["category"] == "contradiction" for w in warnings)

    # Missing image must be recorded in unknown evidence fields with 0 pts
    unknown_fields = risk_data["factor_breakdown"]["unknown_evidence_fields"]
    assert "image_analysis" in unknown_fields
    assert risk_data["factor_breakdown"]["image_score"] == 0


def test_report_snapshot_immutability_and_xss_escaping(client, registered_user, test_assessment):
    """Verify that report snapshots remain immutable and user strings are safely escaped."""
    headers = registered_user["headers"]
    assessment_id = test_assessment["id"]

    # 1. Add symptom with XSS payload
    cough_id = _get_symptom_id(client, "Cough")
    xss_note = "<script>alert('xss')</script><b>Hacking cough</b>"
    client.post(
        f"/api/v1/assessments/{assessment_id}/symptoms",
        headers=headers,
        json={
            "symptom_id": cough_id,
            "severity": "mild",
            "duration_value": 1,
            "duration_unit": "days",
            "notes": xss_note,
        },
    )

    # 2. Generate Report Version 1
    rep1_res = client.post(f"/api/v1/assessments/{assessment_id}/reports", headers=headers)
    assert rep1_res.status_code == 201
    rep1_data = rep1_res.get_json()["data"]
    rep1_id = rep1_data["id"]
    assert rep1_data["report_version"] == 1

    # 3. Add second symptom: Sneezing
    sneeze_id = _get_symptom_id(client, "Sneez")
    client.post(
        f"/api/v1/assessments/{assessment_id}/symptoms",
        headers=headers,
        json={"symptom_id": sneeze_id, "severity": "mild", "duration_value": 1, "duration_unit": "days"},
    )

    # 4. Generate Report Version 2
    rep2_res = client.post(f"/api/v1/assessments/{assessment_id}/reports", headers=headers)
    assert rep2_res.status_code == 201
    rep2_data = rep2_res.get_json()["data"]
    assert rep2_data["report_version"] == 2

    # 5. Fetch Version 1 by ID and verify immutability: must NOT contain sneezing!
    get_v1 = client.get(f"/api/v1/reports/{rep1_id}", headers=headers)
    v1_body = get_v1.get_json()["data"]
    assert v1_body["report_status"] == "ARCHIVED"
    v1_sym_names = [s["name"].lower() for s in v1_body["report_data"]["symptoms"]]
    assert "sneezing" not in v1_sym_names

    # 6. Verify HTML Rendering escapes raw XSS scripts
    html_res = client.get(f"/api/v1/reports/{rep1_id}/html", headers=headers)
    assert html_res.status_code == 200
    html_text = html_res.get_data(as_text=True)
    assert "<script>alert('xss')</script>" not in html_text
    assert "&lt;script&gt;" in html_text

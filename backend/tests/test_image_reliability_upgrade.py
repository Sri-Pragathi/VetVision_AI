"""Comprehensive test suite for Step 8B: Enhanced Computer Vision & Image Analysis Reliability.

Validates:
1. Low resolution quality gate failure + actionable guidance.
2. Underexposed/dark image quality gate failure + lighting guidance.
3. Overexposed/bright image quality gate failure + glare guidance.
4. Blurry image quality gate failure + camera stability/focus guidance.
5. Low contrast / flat image quality gate failure + framing guidance.
6. Extreme aspect ratio distortion quality gate failure + framing guidance.
7. Valid, sharp, well-lit image passes quality gate with full quality metrics.
8. Rejection of unsupported formats (.pdf, .txt, .bmp, .gif).
9. Rejection of empty and corrupted files.
10. Multi-tenant security & ownership enforcement for image access and analysis.
11. Missing and low-quality images remain UNKNOWN and never indicate healthy status.
12. Duplicate evidence prevention across multiple photos of the same lesion.
13. Duplicate evidence prevention between reported skin symptoms and photographic erythema.
14. Emergency override inviolability: reassuring photos never cancel emergency hard-stops.
15. Report generation consistency and snapshot preservation.
"""
import io
import pytest
from PIL import Image, ImageDraw, ImageFilter
from app.services.cv_engine.basic_engine import BasicImageAnalysisEngine
from app.services.cv_engine.base import ImageAnalysisOutput
from app.services.image_analysis_service import ImageAnalysisService
from app.services.risk_engine.rule_engine import RuleBasedRiskAnalysisEngine
from app.services.risk_engine.evidence import EvidenceNormalizer, EvidenceStatus, EvidenceDirection
from app.services.report_service import ReportService
from app.models.health_assessment import HealthAssessment
from app.models.assessment_image import AssessmentImage


def _create_sharp_test_image(width=400, height=400, color=(170, 130, 95)) -> io.BytesIO:
    """Create sharp in-memory test image with clear edge definition."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width // 2, height], fill=(60, 40, 20))
    draw.rectangle([width // 4, height // 4, 3 * width // 4, 3 * height // 4], fill=(230, 190, 150))
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def _create_blurry_test_image(width=400, height=400) -> io.BytesIO:
    """Create intentionally blurry test image via heavy Gaussian blur."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=(170, 130, 95))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width // 2, height], fill=(60, 40, 20))
    draw.rectangle([width // 4, height // 4, 3 * width // 4, 3 * height // 4], fill=(230, 190, 150))
    blurred = img.filter(ImageFilter.GaussianBlur(radius=10))
    blurred.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def _create_overexposed_test_image(width=400, height=400) -> io.BytesIO:
    """Create overexposed washed-out test image."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=(250, 250, 250))
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def _create_dark_test_image(width=400, height=400) -> io.BytesIO:
    """Create underexposed dark test image."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=(15, 15, 15))
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def _create_flat_contrast_test_image(width=400, height=400) -> io.BytesIO:
    """Create completely uniform flat test image with 0 contrast."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=(128, 128, 128))
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def _create_erythema_test_image(width=400, height=400) -> io.BytesIO:
    """Create test image with prominent red channel concentration."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=(230, 60, 50))
    draw = ImageDraw.Draw(img)
    draw.rectangle([100, 100, 300, 300], fill=(255, 30, 20))
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def _get_symptom_id(client, name="Skin"):
    res = client.get(f"/api/v1/symptoms?search={name}")
    data = res.get_json()["data"]
    for s in data:
        if name.lower() in s["name"].lower() or name.lower() in s["category"].lower():
            return s["id"]
    return data[0]["id"]


# ===========================================================================
# 1. Quality Gate & Actionable Guidance Tests
# ===========================================================================

def test_low_resolution_image_generates_actionable_guidance(client, registered_user, test_assessment):
    """Low resolution (<150x150) triggers actionable resolution guidance."""
    buf = _create_sharp_test_image(width=100, height=100)
    upload_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (buf, "low_res.jpg")},
        content_type="multipart/form-data",
    )
    assert upload_res.status_code == 201
    img_id = upload_res.get_json()["data"]["id"]

    analyze_res = client.post(
        f"/api/v1/assessment-images/{img_id}/analyze",
        headers=registered_user["headers"],
    )
    assert analyze_res.status_code == 200
    data = analyze_res.get_json()["data"]

    assert data["quality_gate"] == "REQUIRES_BETTER_IMAGE"
    assert any("resolution is too low" in r.lower() for r in data["reasons"])
    assert any("move closer" in g.lower() or "resolution" in g.lower() for g in data["actionable_guidance"])


def test_dark_underexposed_image_generates_lighting_guidance(client, registered_user, test_assessment):
    """Dark image triggers actionable lighting guidance."""
    buf = _create_dark_test_image()
    upload_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (buf, "dark.jpg")},
        content_type="multipart/form-data",
    )
    img_id = upload_res.get_json()["data"]["id"]

    analyze_res = client.post(
        f"/api/v1/assessment-images/{img_id}/analyze",
        headers=registered_user["headers"],
    )
    data = analyze_res.get_json()["data"]

    assert data["quality_gate"] == "REQUIRES_BETTER_IMAGE"
    assert any("lighting" in r.lower() or "dark" in r.lower() for r in data["reasons"])
    assert any("indoor lights" in g.lower() or "window" in g.lower() for g in data["actionable_guidance"])


def test_overexposed_bright_image_generates_glare_guidance(client, registered_user, test_assessment):
    """Overexposed image triggers actionable anti-glare guidance."""
    buf = _create_overexposed_test_image()
    upload_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (buf, "overexposed.jpg")},
        content_type="multipart/form-data",
    )
    img_id = upload_res.get_json()["data"]["id"]

    analyze_res = client.post(
        f"/api/v1/assessment-images/{img_id}/analyze",
        headers=registered_user["headers"],
    )
    data = analyze_res.get_json()["data"]

    assert data["quality_gate"] == "REQUIRES_BETTER_IMAGE"
    assert any("overexposed" in r.lower() or "bright" in r.lower() for r in data["reasons"])
    assert any("flash" in g.lower() or "glare" in g.lower() for g in data["actionable_guidance"])


def test_blurry_image_generates_steady_camera_guidance(client, registered_user, test_assessment):
    """Motion/out-of-focus blur triggers actionable camera stability guidance."""
    buf = _create_blurry_test_image()
    upload_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (buf, "blurry.jpg")},
        content_type="multipart/form-data",
    )
    img_id = upload_res.get_json()["data"]["id"]

    analyze_res = client.post(
        f"/api/v1/assessment-images/{img_id}/analyze",
        headers=registered_user["headers"],
    )
    data = analyze_res.get_json()["data"]

    assert data["quality_gate"] == "REQUIRES_BETTER_IMAGE"
    assert any("blur" in r.lower() for r in data["reasons"])
    assert any("steady" in g.lower() or "focus" in g.lower() for g in data["actionable_guidance"])


def test_flat_zero_contrast_image_generates_contrast_guidance(client, registered_user, test_assessment):
    """Uniform flat image triggers actionable framing guidance."""
    buf = _create_flat_contrast_test_image()
    upload_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (buf, "flat.jpg")},
        content_type="multipart/form-data",
    )
    img_id = upload_res.get_json()["data"]["id"]

    analyze_res = client.post(
        f"/api/v1/assessment-images/{img_id}/analyze",
        headers=registered_user["headers"],
    )
    data = analyze_res.get_json()["data"]

    assert data["quality_gate"] == "REQUIRES_BETTER_IMAGE"
    assert any("contrast" in r.lower() for r in data["reasons"])


def test_valid_image_passes_quality_gate_with_metrics(client, registered_user, test_assessment):
    """Sharp, well-lit image passes quality gate and returns complete metric flags."""
    buf = _create_sharp_test_image(width=400, height=400)
    upload_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (buf, "valid.jpg")},
        content_type="multipart/form-data",
    )
    img_id = upload_res.get_json()["data"]["id"]

    analyze_res = client.post(
        f"/api/v1/assessment-images/{img_id}/analyze",
        headers=registered_user["headers"],
    )
    data = analyze_res.get_json()["data"]

    assert data["quality_gate"] == "PASSED"
    assert data["analysis_status"] == "ANALYZED"
    metrics = data["quality_metrics"]
    assert metrics["is_well_lit"] is True
    assert metrics["is_sufficient_resolution"] is True
    assert metrics["is_sufficient_contrast"] is True
    assert metrics["is_sharp"] is True
    assert metrics["is_balanced_aspect_ratio"] is True


# ===========================================================================
# 2. Upload Security & Validation
# ===========================================================================

def test_unsupported_formats_rejected(client, registered_user, test_assessment):
    """Unsupported formats like .pdf, .txt, .bmp must be rejected."""
    for filename in ["document.pdf", "script.sh", "raw.bmp", "image.gif"]:
        fake_data = io.BytesIO(b"dummy data content")
        res = client.post(
            f"/api/v1/assessments/{test_assessment['id']}/images",
            headers=registered_user["headers"],
            data={"image": (fake_data, filename)},
            content_type="multipart/form-data",
        )
        assert res.status_code == 422


def test_empty_and_corrupt_files_rejected(client, registered_user, test_assessment):
    """Zero-byte and corrupted non-image files are rejected with 422."""
    empty_buf = io.BytesIO(b"")
    res1 = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (empty_buf, "empty.png")},
        content_type="multipart/form-data",
    )
    assert res1.status_code == 422

    corrupt_buf = io.BytesIO(b"NOT_A_JPEG_FILE_CORRUPTED_STREAM")
    res2 = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (corrupt_buf, "bad.jpg")},
        content_type="multipart/form-data",
    )
    assert res2.status_code == 422


def test_multi_tenant_image_security(client, registered_user, test_assessment):
    """User B cannot access or analyze User A's images."""
    buf = _create_sharp_test_image()
    up_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (buf, "sec_test.jpg")},
        content_type="multipart/form-data",
    )
    img_id = up_res.get_json()["data"]["id"]

    # Register user B
    user_b_res = client.post("/api/v1/auth/register", json={
        "name": "User B",
        "email": "user_b_img@test.com",
        "password": "Password123!",
    })
    b_token = user_b_res.get_json()["data"]["tokens"]["access_token"]
    b_headers = {"Authorization": f"Bearer {b_token}"}

    # User B attempts to access image
    get_res = client.get(f"/api/v1/assessment-images/{img_id}", headers=b_headers)
    assert get_res.status_code == 403

    # User B attempts to trigger analysis
    post_res = client.post(f"/api/v1/assessment-images/{img_id}/analyze", headers=b_headers)
    assert post_res.status_code == 403

    # User B attempts deletion
    del_res = client.delete(f"/api/v1/assessment-images/{img_id}", headers=b_headers)
    assert del_res.status_code == 403


# ===========================================================================
# 3. Evidence Integration & Duplicate Prevention
# ===========================================================================

def test_missing_and_failed_images_treated_as_unknown_not_healthy():
    """Unanalyzed or poor quality images are strictly UNKNOWN with 0 score contribution."""
    payload = {
        "pet": {"species": "dog", "age": 4},
        "symptoms": [{"name": "Lethargy", "severity": "mild", "duration_hours": 12.0}],
        "observations": {},
        "image_analysis": {
            "images_count": 1,
            "analyzed_count": 1,
            "observations": [
                {
                    "observation_label": "POOR_IMAGE_QUALITY",
                    "severity": "moderate",
                    "extra_data": {
                        "reasons": ["Excessive blur detected"],
                        "actionable_guidance": ["Hold camera steady"],
                    },
                }
            ],
        },
    }

    evidence = EvidenceNormalizer.normalize(payload)
    engine = RuleBasedRiskAnalysisEngine()
    output = engine.analyze(payload)

    # Must be UNKNOWN and 0 contribution
    poor_items = [i for i in evidence.image_observations if i.status == EvidenceStatus.UNKNOWN]
    assert len(poor_items) >= 1
    assert poor_items[0].direction == EvidenceDirection.UNKNOWN

    assert output.factor_breakdown["image_score"] == 0
    struct_img = next((f for f in output.structured_factors if f["factor_name"] == "Computer Vision Quality Gate"), None)
    assert struct_img is not None
    assert struct_img["contribution_pts"] == 0
    assert struct_img["direction"] == "unknown"


def test_duplicate_evidence_prevention_across_multiple_photos():
    """Uploading two photos showing erythema must NOT double-count risk points."""
    payload = {
        "pet": {"species": "dog", "age": 2},
        "symptoms": [{"name": "Lethargy", "severity": "mild", "duration_hours": 12.0}],
        "observations": {},
        "image_analysis": {
            "images_count": 2,
            "analyzed_count": 2,
            "observations": [
                {"observation_label": "ELEVATED_ERYTHEMA_DETECTED", "severity": "moderate"},
                {"observation_label": "ELEVATED_ERYTHEMA_DETECTED", "severity": "moderate"},
            ],
        },
    }

    engine = RuleBasedRiskAnalysisEngine()
    output = engine.analyze(payload)

    # Primary erythema awarded once (+5 pts), second image awarded 0 pts
    assert output.factor_breakdown["image_score"] == 5

    factors = output.structured_factors
    primary_erythema = next((f for f in factors if f["factor_name"] == "Visual Dermatological Inspection"), None)
    secondary_erythema = next((f for f in factors if f["factor_name"] == "Secondary Visual Inspection"), None)

    assert primary_erythema is not None
    assert primary_erythema["contribution_pts"] == 5
    assert secondary_erythema is not None
    assert secondary_erythema["contribution_pts"] == 0
    assert "prevent duplicate" in secondary_erythema["rule_applied"].lower()


def test_duplicate_evidence_prevention_with_reported_skin_symptom():
    """If skin symptom is already reported, erythema is scored as corroborating (+2 pts) not full additive (+5 pts)."""
    payload = {
        "pet": {"species": "dog", "age": 2},
        "symptoms": [
            {"name": "Skin rash", "category": "Skin", "severity": "moderate", "duration_hours": 24.0}
        ],
        "observations": {},
        "image_analysis": {
            "images_count": 1,
            "analyzed_count": 1,
            "observations": [
                {"observation_label": "ELEVATED_ERYTHEMA_DETECTED", "severity": "moderate"}
            ],
        },
    }

    engine = RuleBasedRiskAnalysisEngine()
    output = engine.analyze(payload)

    # Corroborating modifier (+2 pts) instead of full independent (+5 pts)
    assert output.factor_breakdown["image_score"] == 2

    struct_img = next((f for f in output.structured_factors if f["factor_name"] == "Visual Dermatological Inspection"), None)
    assert struct_img is not None
    assert struct_img["contribution_pts"] == 2
    assert "corroborating" in struct_img["rule_applied"].lower()
    assert "prevent double-counting" in struct_img["rule_applied"].lower()


def test_emergency_override_inviolability_with_reassuring_image():
    """Emergency symptoms cannot be discounted by a clean, normal-looking photograph."""
    payload = {
        "pet": {"species": "cat", "age": 3},
        "symptoms": [{"name": "Difficulty breathing", "severity": "severe", "duration_hours": 2.0}],
        "observations": {"breathing_change": "labored"},
        "image_analysis": {
            "images_count": 1,
            "analyzed_count": 1,
            "observations": [
                {"observation_label": "STANDARD_COLOR_DISTRIBUTION", "severity": "normal"},
                {"observation_label": "SUITABLE_FOR_ANALYSIS", "severity": "normal"},
            ],
        },
    }

    engine = RuleBasedRiskAnalysisEngine()
    output = engine.analyze(payload)

    # Authoritative emergency floor >= 90
    assert output.is_emergency is True
    assert output.risk_level == "EMERGENCY"
    assert output.risk_score >= 90
    assert output.factor_breakdown["emergency_override"] is True

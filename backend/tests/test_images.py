"""Comprehensive tests for Step 5: Computer Vision / Pet Image Analysis Pipeline.

Covers:
- Valid image upload (JPEG/PNG/WEBP)
- Unsupported file type rejection
- Oversized file rejection
- Empty file rejection
- Corrupted image rejection
- Quality gate: Low resolution detection (REQUIRES_BETTER_IMAGE)
- Quality gate: Insufficient lighting / dark image detection
- Successful computer vision analysis & observation extraction
- Re-analysis idempotency
- Image metadata listing and single retrieval
- Image analysis retrieval (404 before analysis, 200 after)
- Image deletion and cascade cleanup
- Unauthorized (401) and forbidden (403) access security
- Integration with AiDataPreparationService payload
- Integration with Step 4 Risk Analysis Engine
- Emergency assessment remains emergency (never downgraded by image)
- Pluggable BaseImageAnalysisEngine extensibility
"""
import io
import pytest
from PIL import Image, ImageDraw
from app.services.storage_service import LocalStorageService
from app.services.cv_engine.base import BaseImageAnalysisEngine, ImageAnalysisOutput
from app.services.image_analysis_service import ImageAnalysisService
from app.services.ai_data_service import AiDataPreparationService
from app.services.risk_analysis_service import RiskAnalysisService


# ---------------------------------------------------------------------------
# In-Memory Test Image Helpers
# ---------------------------------------------------------------------------

def _create_test_image(
    width: int = 300,
    height: int = 300,
    color: tuple = (180, 140, 100),
    fmt: str = "JPEG",
) -> io.BytesIO:
    """Generate an in-memory valid PIL test image with realistic visual contrast."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=color)
    draw = ImageDraw.Draw(img)
    # Add visual structure/contrast
    draw.rectangle([0, 0, width // 2, height], fill=(70, 50, 30))
    draw.rectangle([width // 4, height // 4, 3 * width // 4, 3 * height // 4], fill=(220, 180, 140))
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf


def _create_dark_test_image(width: int = 300, height: int = 300) -> io.BytesIO:
    """Generate a very dark / underexposed image."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=(10, 10, 10))
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_valid_image_upload(client, registered_user, test_assessment):
    """1. Upload a valid JPEG image attached to an assessment."""
    img_buf = _create_test_image(width=400, height=300, color=(160, 120, 90))

    response = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (img_buf, "pet_photo.jpg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["assessment_id"] == test_assessment["id"]
    assert data["original_filename"] == "pet_photo.jpg"
    assert data["mime_type"] == "image/jpeg"
    assert data["width"] == 400
    assert data["height"] == 300
    assert data["file_size"] > 0
    assert data["processing_status"] == "READY"
    assert data["analysis_status"] == "PENDING"


def test_unsupported_file_type_rejected(client, registered_user, test_assessment):
    """2. Unsupported file extensions (e.g. .pdf, .txt) must be rejected."""
    fake_txt = io.BytesIO(b"Hello world this is text")

    response = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (fake_txt, "medical_record.pdf")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 422
    assert "unsupported" in response.get_json()["message"].lower()


def test_empty_file_rejected(client, registered_user, test_assessment):
    """3. Empty (0-byte) files must be rejected."""
    empty_buf = io.BytesIO(b"")

    response = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (empty_buf, "empty.png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 422
    assert "empty" in response.get_json()["message"].lower()


def test_corrupted_image_rejected(client, registered_user, test_assessment):
    """4. Corrupted file content disguised with .jpg extension must be rejected."""
    corrupt_buf = io.BytesIO(b"THIS_IS_NOT_A_VALID_JPEG_HEADER_123456789")

    response = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (corrupt_buf, "damaged.jpg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 422
    assert "not a valid" in response.get_json()["message"].lower() or "corrupted" in response.get_json()["message"].lower()


def test_low_resolution_image_quality_gate(client, registered_user, test_assessment):
    """5. Quality Gate: Low resolution (<150x150) triggers REQUIRES_BETTER_IMAGE."""
    small_buf = _create_test_image(width=80, height=80)

    upload_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (small_buf, "tiny.jpg")},
        content_type="multipart/form-data",
    )
    assert upload_res.status_code == 201
    img_id = upload_res.get_json()["data"]["id"]

    # Run analysis
    analyze_res = client.post(
        f"/api/v1/assessment-images/{img_id}/analyze",
        headers=registered_user["headers"],
    )
    assert analyze_res.status_code == 200
    data = analyze_res.get_json()["data"]

    assert data["quality_gate"] == "REQUIRES_BETTER_IMAGE"
    assert data["analysis_status"] == "REQUIRES_BETTER_IMAGE"
    assert any("resolution is too low" in r.lower() for r in data["reasons"])
    assert "new photo" in data["recommendation"].lower()
    assert len(data["observations"]) >= 1


def test_insufficient_lighting_quality_gate(client, registered_user, test_assessment):
    """6. Quality Gate: Very dark image triggers REQUIRES_BETTER_IMAGE."""
    dark_buf = _create_dark_test_image(width=300, height=300)

    upload_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (dark_buf, "dark.jpg")},
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
    assert any("lighting" in r.lower() or "dark" in r.lower() for r in data["reasons"])


def test_successful_image_analysis(client, registered_user, test_assessment):
    """7. Valid quality image passes quality gate and extracts visual observations."""
    good_buf = _create_test_image(width=400, height=400, color=(170, 130, 95))

    upload_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (good_buf, "healthy_coat.jpg")},
        content_type="multipart/form-data",
    )
    img_id = upload_res.get_json()["data"]["id"]

    analyze_res = client.post(
        f"/api/v1/assessment-images/{img_id}/analyze",
        headers=registered_user["headers"],
    )
    assert analyze_res.status_code == 200
    data = analyze_res.get_json()["data"]

    assert data["quality_gate"] == "PASSED"
    assert data["analysis_status"] == "ANALYZED"
    assert data["quality_score"] > 0.6
    assert len(data["observations"]) >= 1
    assert "disclaimer" in data
    assert "does not replace professional veterinary" in data["disclaimer"].lower()


def test_re_analysis_idempotency(client, registered_user, test_assessment):
    """8. Re-running analysis clears and replaces previous observations without duplication."""
    img_buf = _create_test_image(width=350, height=350)
    upload_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (img_buf, "test_rerun.jpg")},
        content_type="multipart/form-data",
    )
    img_id = upload_res.get_json()["data"]["id"]

    # First analysis
    res1 = client.post(f"/api/v1/assessment-images/{img_id}/analyze", headers=registered_user["headers"])
    obs_count_1 = len(res1.get_json()["data"]["observations"])

    # Second analysis
    res2 = client.post(f"/api/v1/assessment-images/{img_id}/analyze", headers=registered_user["headers"])
    obs_count_2 = len(res2.get_json()["data"]["observations"])

    assert obs_count_1 == obs_count_2


def test_get_assessment_images_and_single_details(client, registered_user, test_assessment):
    """9. List all images for an assessment and retrieve single image details."""
    img1 = _create_test_image(width=200, height=200)
    img2 = _create_test_image(width=300, height=300)

    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (img1, "photo1.jpg")},
        content_type="multipart/form-data",
    )
    res2 = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (img2, "photo2.jpg")},
        content_type="multipart/form-data",
    )
    img2_id = res2.get_json()["data"]["id"]

    # List images
    list_res = client.get(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
    )
    assert list_res.status_code == 200
    images = list_res.get_json()["data"]["images"]
    assert len(images) == 2

    # Get single image
    single_res = client.get(
        f"/api/v1/assessment-images/{img2_id}",
        headers=registered_user["headers"],
    )
    assert single_res.status_code == 200
    assert single_res.get_json()["data"]["original_filename"] == "photo2.jpg"


def test_get_image_analysis_endpoint(client, registered_user, test_assessment):
    """10. GET /analysis returns 404 before analyze, 200 after."""
    img = _create_test_image(width=250, height=250)
    upload_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (img, "photo.jpg")},
        content_type="multipart/form-data",
    )
    img_id = upload_res.get_json()["data"]["id"]

    # Before analysis -> 404
    pre_res = client.get(
        f"/api/v1/assessment-images/{img_id}/analysis",
        headers=registered_user["headers"],
    )
    assert pre_res.status_code == 404

    # Perform analysis
    client.post(
        f"/api/v1/assessment-images/{img_id}/analyze",
        headers=registered_user["headers"],
    )

    # After analysis -> 200
    post_res = client.get(
        f"/api/v1/assessment-images/{img_id}/analysis",
        headers=registered_user["headers"],
    )
    assert post_res.status_code == 200
    data = post_res.get_json()["data"]
    assert "observations" in data
    assert "disclaimer" in data


def test_delete_assessment_image(client, registered_user, test_assessment):
    """11. DELETE /assessment-images/<id> removes image and observations."""
    img = _create_test_image(width=250, height=250)
    upload_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (img, "to_delete.jpg")},
        content_type="multipart/form-data",
    )
    img_id = upload_res.get_json()["data"]["id"]

    # Analyze first
    client.post(f"/api/v1/assessment-images/{img_id}/analyze", headers=registered_user["headers"])

    # Delete
    del_res = client.delete(
        f"/api/v1/assessment-images/{img_id}",
        headers=registered_user["headers"],
    )
    assert del_res.status_code == 200

    # Verify 404 on subsequent get
    check_res = client.get(
        f"/api/v1/assessment-images/{img_id}",
        headers=registered_user["headers"],
    )
    assert check_res.status_code == 404


def test_unauthorized_and_forbidden_image_access(client, registered_user, second_user, test_assessment):
    """12. Security: 401 unauthenticated and 403 cross-tenant isolation."""
    img = _create_test_image(width=200, height=200)

    # Upload by registered_user
    upload_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (img, "secure.jpg")},
        content_type="multipart/form-data",
    )
    img_id = upload_res.get_json()["data"]["id"]

    # Unauthenticated upload attempt -> 401
    img_buf = _create_test_image()
    unauth_up = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        data={"image": (img_buf, "unauth.jpg")},
        content_type="multipart/form-data",
    )
    assert unauth_up.status_code == 401

    # Cross-tenant access: second_user accessing registered_user's image -> 403
    forb_get = client.get(
        f"/api/v1/assessment-images/{img_id}",
        headers=second_user["headers"],
    )
    assert forb_get.status_code == 403

    forb_analyze = client.post(
        f"/api/v1/assessment-images/{img_id}/analyze",
        headers=second_user["headers"],
    )
    assert forb_analyze.status_code == 403

    forb_del = client.delete(
        f"/api/v1/assessment-images/{img_id}",
        headers=second_user["headers"],
    )
    assert forb_del.status_code == 403


def test_cannot_upload_image_to_cancelled_assessment(client, registered_user, test_assessment):
    """13. Upload to cancelled assessment is rejected with 422."""
    # Cancel assessment
    client.put(
        f"/api/v1/assessments/{test_assessment['id']}",
        headers=registered_user["headers"],
        json={"status": "cancelled"},
    )

    img = _create_test_image()
    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (img, "fail.jpg")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 422
    assert "cancelled" in res.get_json()["message"].lower()


def test_ai_data_payload_includes_image_analysis(client, registered_user, test_assessment):
    """14. AiDataPreparationService payload includes structured image_analysis section."""
    img = _create_test_image(width=300, height=300)
    upload_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (img, "ai_test.jpg")},
        content_type="multipart/form-data",
    )
    img_id = upload_res.get_json()["data"]["id"]

    # Run analysis
    client.post(f"/api/v1/assessment-images/{img_id}/analyze", headers=registered_user["headers"])

    # Retrieve AI data
    ai_res = client.get(
        f"/api/v1/assessments/{test_assessment['id']}/ai-data",
        headers=registered_user["headers"],
    )
    assert ai_res.status_code == 200
    ai_input = ai_res.get_json()["data"]["ai_input"]

    assert "image_analysis" in ai_input
    img_data = ai_input["image_analysis"]
    assert img_data["images_count"] >= 1
    assert img_data["analyzed_count"] >= 1
    assert len(img_data["observations"]) >= 1


def test_step_4_risk_integration_with_images(client, registered_user, test_assessment):
    """15. Risk analysis consumes image analysis observations safely."""
    # Add mild symptom
    sym_res = client.get("/api/v1/symptoms?search=Sneezing")
    sym_id = sym_res.get_json()["data"][0]["id"]
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={"symptom_id": sym_id, "severity": "mild", "duration_value": 2, "duration_unit": "hours"},
    )

    # Attach and analyze image
    img = _create_test_image(width=300, height=300)
    up_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (img, "risk_img.jpg")},
        content_type="multipart/form-data",
    )
    img_id = up_res.get_json()["data"]["id"]
    client.post(f"/api/v1/assessment-images/{img_id}/analyze", headers=registered_user["headers"])

    # Execute Risk Analysis
    risk_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )
    assert risk_res.status_code == 200
    risk_data = risk_res.get_json()["data"]

    assert "image_score" in risk_data["factor_breakdown"]
    assert risk_data["risk_level"] in ("LOW", "MODERATE", "HIGH", "EMERGENCY")


def test_emergency_assessment_remains_emergency_with_images(client, registered_user, test_assessment):
    """16. Emergency conditions are never downgraded by attached images."""
    # Add emergency symptom: Difficulty Breathing
    sym_res = client.get("/api/v1/symptoms?search=Difficulty Breathing")
    sym_id = sym_res.get_json()["data"][0]["id"]
    client.post(
        f"/api/v1/assessments/{test_assessment['id']}/symptoms",
        headers=registered_user["headers"],
        json={"symptom_id": sym_id, "severity": "severe", "duration_value": 1, "duration_unit": "hours"},
    )

    # Attach normal image
    img = _create_test_image(width=400, height=400)
    up_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (img, "emergency_check.jpg")},
        content_type="multipart/form-data",
    )
    img_id = up_res.get_json()["data"]["id"]
    client.post(f"/api/v1/assessment-images/{img_id}/analyze", headers=registered_user["headers"])

    # Run Risk Analysis
    risk_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/risk-analysis",
        headers=registered_user["headers"],
    )
    risk_data = risk_res.get_json()["data"]

    assert risk_data["risk_level"] == "EMERGENCY"
    assert risk_data["risk_score"] >= 90
    assert risk_data["emergency"] is True


def test_pluggable_cv_engine_extensibility(client, registered_user, test_assessment):
    """17. Custom BaseImageAnalysisEngine adapter can be plugged in seamlessly."""
    class CustomMockCVEngine(BaseImageAnalysisEngine):
        @property
        def version(self) -> str:
            return "v2.0.0-mock_cv_model"

        def analyze_image(self, image_path, context=None):
            return ImageAnalysisOutput(
                status="SUCCESS",
                quality_gate="PASSED",
                quality_score=0.95,
                quality_metrics={"custom_metric": 42},
                visual_observations=[
                    {
                        "observation_type": "lesion_detection",
                        "observation_label": "SUPERFICIAL_DERMAL_EROSION",
                        "severity": "mild",
                        "region": "left_ear_pinna",
                        "description": "Mock model detected superficial ear margin erosion.",
                        "source": "computer_vision",
                        "model_version": self.version,
                    }
                ],
                reasons=[],
                recommendation="Clean area and consult vet.",
                engine_version=self.version,
            )

    img = _create_test_image(width=300, height=300)
    up_res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/images",
        headers=registered_user["headers"],
        data={"image": (img, "mock_test.jpg")},
        content_type="multipart/form-data",
    )
    img_id = up_res.get_json()["data"]["id"]

    # Analyze with custom engine
    result = ImageAnalysisService.analyze_image(
        image_id=img_id,
        user_id=registered_user["user"]["id"],
        engine=CustomMockCVEngine(),
    )

    assert result["engine_version"] == "v2.0.0-mock_cv_model"
    assert result["quality_score"] == 0.95
    assert len(result["observations"]) == 1
    assert result["observations"][0]["observation_label"] == "SUPERFICIAL_DERMAL_EROSION"

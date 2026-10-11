"""Integration tests for secure image persistence and role-authorized file access."""
import io
import uuid
import pytest
from PIL import Image
from app.extensions import db
from app.models.user import User
from app.models.pet import Pet
from app.models.health_assessment import HealthAssessment
from app.models.assessment_image import AssessmentImage


def _create_sample_png() -> io.BytesIO:
    """Generate a small valid PNG in memory."""
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color=(100, 150, 200))
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


@pytest.fixture
def other_user(client):
    """Create a second registered user for tenancy isolation checks."""
    email = f"other_{uuid.uuid4().hex[:6]}@example.com"
    password = "ValidPassword123!"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"name": "Other Owner", "email": email, "password": password},
    )
    assert reg_res.status_code == 201
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.get_json()["data"]["tokens"]["access_token"]
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "user_id": login_res.get_json()["data"]["user"]["id"],
    }



def test_pet_avatar_upload_and_stream(client, registered_user, test_pet):
    """Verify owner can upload and retrieve pet avatar image file."""
    headers = registered_user["headers"]
    pet_id = test_pet["id"]

    img_buf = _create_sample_png()
    upload_res = client.post(
        f"/api/v1/pets/{pet_id}/avatar",
        headers=headers,
        data={"image": (img_buf, "milo_avatar.png")},
    )
    assert upload_res.status_code == 200
    data = upload_res.get_json()
    assert data["success"] is True
    assert f"/api/v1/pets/{pet_id}/avatar" in data["data"]["photo_url"]

    # Stream avatar file
    stream_res = client.get(f"/api/v1/pets/{pet_id}/avatar", headers=headers)
    assert stream_res.status_code == 200
    assert "image/png" in stream_res.content_type
    assert len(stream_res.data) > 0


def test_pet_avatar_authorization_isolation(client, registered_user, other_user, test_pet):
    """Verify other users cannot access pet avatar, strictly isolated to pet owner."""
    owner_headers = registered_user["headers"]
    pet_id = test_pet["id"]

    # Upload avatar
    img_buf = _create_sample_png()
    client.post(
        f"/api/v1/pets/{pet_id}/avatar",
        headers=owner_headers,
        data={"image": (img_buf, "avatar.png")},
    )

    # 1. Unauthenticated request -> 401
    res_unauth = client.get(f"/api/v1/pets/{pet_id}/avatar")
    assert res_unauth.status_code == 401

    # 2. Other user -> 403 Forbidden
    res_forbidden = client.get(f"/api/v1/pets/{pet_id}/avatar", headers=other_user["headers"])
    assert res_forbidden.status_code == 403

    # 3. Owning Pet Owner -> 200 OK
    res_owner = client.get(f"/api/v1/pets/{pet_id}/avatar", headers=owner_headers)
    assert res_owner.status_code == 200
    assert len(res_owner.data) > 0


def test_assessment_image_file_streaming_and_isolation(
    client, registered_user, other_user, test_assessment
):
    """Verify assessment image file streaming with owner access and non-owner isolation."""
    headers = registered_user["headers"]
    assessment_id = test_assessment["id"]

    # Upload an assessment image
    img_buf = _create_sample_png()
    up_res = client.post(
        f"/api/v1/assessments/{assessment_id}/images",
        headers=headers,
        data={
            "image": (img_buf, "ear_infection.png"),
            "body_part": "ear",
        },
    )
    assert up_res.status_code == 201
    image_id = up_res.get_json()["data"]["id"]

    # 1. Owner streaming -> 200 OK
    res_owner = client.get(f"/api/v1/assessment-images/{image_id}/file", headers=headers)
    assert res_owner.status_code == 200
    assert len(res_owner.data) > 0

    # 2. Other owner streaming -> 403 Forbidden
    res_other = client.get(f"/api/v1/assessment-images/{image_id}/file", headers=other_user["headers"])
    assert res_other.status_code == 403

    # 3. Unauthenticated -> 401
    res_unauth = client.get(f"/api/v1/assessment-images/{image_id}/file")
    assert res_unauth.status_code == 401

"""Tests for GuidanceAssistantService and /api/v1/guidance API endpoints."""
import pytest
from app.services.groq_service import GroqService


@pytest.fixture(autouse=True)
def disable_groq_for_deterministic_tests(monkeypatch):
    """Ensure guidance assistant tests verify deterministic fallback logic."""
    monkeypatch.setattr(GroqService, "is_available", classmethod(lambda cls: False))


@pytest.fixture
def test_setup(client, registered_user, second_user):
    """Setup test user, auth token, and pet."""
    # Create Pet for registered_user (Cat)
    pet_res = client.post(
        "/api/v1/pets",
        headers=registered_user["headers"],
        json={
            "name": "Luna",
            "species": "Cat",
            "breed": "Siamese",
            "weight": 4.2,
        },
    )
    assert pet_res.status_code == 201
    pet_id = pet_res.get_json()["data"]["id"]

    return {
        "headers": registered_user["headers"],
        "user": registered_user["user"],
        "headers2": second_user["headers"],
        "pet_id": pet_id,
    }


def test_quick_questions_endpoint(client, test_setup):
    """Test retrieving quick question templates."""
    # Unauthenticated should succeed (public templates)
    res = client.get("/api/v1/guidance/quick-questions")
    assert res.status_code == 200
    assert "questions" in res.get_json()["data"]

    # Authenticated
    res = client.get("/api/v1/guidance/quick-questions", headers=test_setup["headers"])
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "questions" in data
    assert len(data["questions"]) >= 5
    assert any("vomited" in q["question"] for q in data["questions"])


def test_ask_unauthenticated_general_query(client):
    """Test that general questions without auth token receive supportive guidance."""
    res = client.post("/api/v1/guidance/ask", json={
        "question": "What should I do if my dog vomited once?",
    })
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "answer" in data
    assert len(data["answer"]) > 10
    assert "WITHHOLD FOOD" in data["answer"] or "water" in data["answer"].lower()


def test_ask_validation_missing_question(client, test_setup):
    """Test validation errors for empty or missing question."""
    res = client.post("/api/v1/guidance/ask", headers=test_setup["headers"], json={
        "question": "",
    })
    assert res.status_code == 422


def test_ask_foreign_pet_forbidden(client, test_setup):
    """Test that accessing another owner's pet is rejected with 403 Forbidden."""
    res = client.post("/api/v1/guidance/ask", headers=test_setup["headers2"], json={
        "pet_id": test_setup["pet_id"],
        "question": "How is my cat doing?",
    })
    assert res.status_code == 403


def test_ask_human_medication_emergency_warning(client, test_setup):
    """Test inquiry about human medication triggers emergency warning and strict contraindications."""
    res = client.post("/api/v1/guidance/ask", headers=test_setup["headers"], json={
        "pet_id": test_setup["pet_id"],
        "question": "Can I give Luna a small piece of paracetamol or Tylenol for pain?",
    })
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["urgency_level"] == "EMERGENCY"
    assert "DO NOT give Luna any human pain relievers" in data["answer"]
    assert "methemoglobinemia" in data["answer"]  # Species-specific cat toxicity
    assert any("paracetamol" in c.lower() for c in data["contraindications"])
    assert "aspca_poison_control" in data["emergency_contacts"]


def test_ask_induce_vomiting_contraindication(client, test_setup):
    """Test inquiry about inducing vomiting at home triggers critical harm warning."""
    res = client.post("/api/v1/guidance/ask", headers=test_setup["headers"], json={
        "pet_id": test_setup["pet_id"],
        "question": "Should I make my pet throw up with hydrogen peroxide?",
    })
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["urgency_level"] == "EMERGENCY"
    assert "DO NOT attempt to induce vomiting" in data["answer"]
    assert "esophagus" in data["answer"]
    assert any("salt" in c.lower() or "peroxide" in c.lower() for c in data["contraindications"])


def test_ask_after_hours_closed_clinic(client, test_setup):
    """Test night/after-hours query provides 24-hr triage steps and hospital locator."""
    res = client.post("/api/v1/guidance/ask", headers=test_setup["headers"], json={
        "pet_id": test_setup["pet_id"],
        "question": "It is midnight and my regular clinic is closed. What should I do first?",
    })
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "gum color" in data["answer"]
    assert "24-hour veterinary emergency hospital" in data["answer"]
    assert "call the emergency hospital while on your way" in data["answer"].lower()
    assert "https://www.aaha.org/your-pet/find-a-hospital/" in data["emergency_contacts"]["aaha_hospital_locator"]


def test_ask_single_vomit_monitoring(client, test_setup):
    """Test single vomit inquiry returns supportive food rest and hydration guidance."""
    res = client.post("/api/v1/guidance/ask", headers=test_setup["headers"], json={
        "pet_id": test_setup["pet_id"],
        "question": "Luna vomited once today. What should I monitor?",
    })
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["urgency_level"] in ["HOME_MONITORING", "LOW"]
    assert "WITHHOLD FOOD" in data["answer"]
    assert "small amounts of clean room-temperature water" in data["answer"]
    assert data["pet_context"]["name"] == "Luna"
    assert data["pet_context"]["species"] == "Cat"


def test_ask_out_of_topic_query_politely_rejected(client, test_setup):
    """Test that non-pet queries (math, trivia, coding) are politely rejected."""
    for off_topic_q in [
        "What is the capital of France?",
        "Write a python script to sort an array",
        "Who is the president of the United States?",
        "What is 25 * 4?",
    ]:
        res = client.post("/api/v1/guidance/ask", json={"question": off_topic_q})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert data["urgency_level"] == "GENERAL_INFO"
        assert "specialized exclusively in pet health" in data["answer"].lower() or "cannot assist with questions outside of pet" in data["answer"].lower()
        assert len(data["contraindications"]) == 0


def test_ask_safe_fruits_nutrition_guidance(client, test_setup):
    """Test nutrition query regarding blueberries and safe fruits returns helpful dietary advice."""
    res = client.post("/api/v1/guidance/ask", headers=test_setup["headers"], json={
        "pet_id": test_setup["pet_id"],
        "question": "Can my pet safely eat blueberries and apples?",
    })
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "Blueberries" in data["answer"]
    assert "Apples" in data["answer"]
    assert any("blueberries" in k.lower() for k in data["key_takeaways"])


def test_ask_ear_itching_guidance(client, test_setup):
    """Test ear scratching inquiry returns ear mites, infection triage, and Q-tip contraindication."""
    res = client.post("/api/v1/guidance/ask", headers=test_setup["headers"], json={
        "pet_id": test_setup["pet_id"],
        "question": "Why is my cat constantly scratching her ears and shaking her head?",
    })
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "Ear Infections" in data["answer"] or "Ear Mites" in data["answer"]
    assert any("q-tip" in c.lower() for c in data["contraindications"])


def test_ask_vaccination_schedule_guidance(client):
    """Test puppy/kitten vaccination schedule query returns age milestones."""
    res = client.post("/api/v1/guidance/ask", json={
        "question": "What is the recommended core vaccination schedule for a puppy?",
    })
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "DHPP" in data["answer"]
    assert "Rabies" in data["answer"]
    assert "6 to 8 Weeks" in data["answer"]


def test_ask_rabbit_daily_pet_care(client):
    """Test specific inquiry about rabbit care provides hay diet and GI stasis awareness."""
    res = client.post("/api/v1/guidance/ask", json={
        "question": "How do I take care of a rabbit and what should they eat?",
    })
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "Timothy hay" in data["answer"]
    assert "Stasis" in data["answer"]


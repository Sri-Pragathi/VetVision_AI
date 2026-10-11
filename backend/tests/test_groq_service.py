"""Tests for GroqService and AI integration in VetVision AI."""
from unittest.mock import patch
import pytest
from app.services.groq_service import GroqService
from app.services.guidance_service import GuidanceAssistantService


def test_groq_service_placeholder_key_detected_as_unavailable(monkeypatch, app):
    """Verify that template placeholder keys are safely detected as unavailable."""
    monkeypatch.setenv("GROQ_API_KEY", "your_groq_api_key_here")
    app.config["GROQ_API_KEY"] = "your_groq_api_key_here"
    assert GroqService.is_available() is False

    monkeypatch.setenv("GROQ_API_KEY", "")
    app.config["GROQ_API_KEY"] = ""
    assert GroqService.is_available() is False


def test_groq_service_valid_key_detected_as_available(monkeypatch, app):
    """Verify that a configured key is detected as available."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_mock_valid_key_12345678")
    app.config["GROQ_API_KEY"] = "gsk_test_mock_valid_key_12345678"
    assert GroqService.is_available() is True
    assert GroqService.get_model() in ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]


def test_groq_service_network_error_handled_gracefully(monkeypatch):
    """Verify that GroqService handles network errors gracefully without crashing."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_mock_valid_key_12345678")
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        res = GroqService.call_chat_completion([{"role": "user", "content": "Hello"}])
        assert res is None


def test_guidance_assistant_uses_groq_when_available(monkeypatch, registered_user):
    """Verify that GuidanceAssistantService uses Groq response when API returns content."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_mock_valid_key_12345678")

    simulated_groq_reply = (
        "Hello! I am VetVision AI powered by Groq. "
        "For your cat, keep her comfortable and hydrated. "
        "Strictly never give human pain medicines like paracetamol or Tylenol."
    )

    with patch.object(GroqService, "is_available", return_value=True):
        with patch.object(GroqService, "generate_pet_guidance", return_value=simulated_groq_reply):
            result = GuidanceAssistantService.ask(
                user_id=registered_user["user"]["id"],
                question="What should I do for my pet?",
            )
            assert result["answer"] == simulated_groq_reply
            assert "Groq AI" in result["ai_engine"]
            assert "emergency_contacts" in result


def test_guidance_assistant_falls_back_when_groq_unavailable(monkeypatch, registered_user):
    """Verify seamless deterministic fallback when Groq key is placeholder or unset."""
    monkeypatch.setenv("GROQ_API_KEY", "your_groq_api_key_here")

    with patch.object(GroqService, "is_available", return_value=False):
        result = GuidanceAssistantService.ask(
            user_id=registered_user["user"]["id"],
            question="Can I give my pet paracetamol?",
        )
        assert "DO NOT give" in result["answer"]
        assert "Deterministic Fallback" in result["ai_engine"]
        assert result["urgency_level"] == "EMERGENCY"


def test_guardrails_purge_asterisks_and_markdown():
    """Verify that all single and double asterisks and markdown hashes are completely stripped."""
    raw = "**Immediate Guidance**\n- **Do NOT** give *Luna* paracetamol.\n### WHAT TO WATCH FOR:\n- Lethargy and vomiting."
    sanitized = GroqService.apply_guardrails_and_sanitize(raw, "Can I give paracetamol?")
    assert "*" not in sanitized
    assert "###" not in sanitized
    assert "Immediate Guidance" in sanitized
    assert "Do NOT give Luna paracetamol." in sanitized


def test_guardrails_override_unsafe_medication_response():
    """Verify that medication questions lacking strict refusal trigger safety override."""
    unsafe_reply = "You can crush a small pill into some wet food for pain relief."
    sanitized = GroqService.apply_guardrails_and_sanitize(
        unsafe_reply,
        question="Can I give Luna some paracetamol?",
        pet_name="Luna",
        species="Cat",
    )
    assert "STRICT SAFETY WARNING" in sanitized
    assert "Never give Luna human pain relievers" in sanitized
    assert "fatal to cats" in sanitized


def test_guardrails_override_unsafe_induce_vomiting_response():
    """Verify that induce vomiting inquiries trigger critical safety refusal."""
    unsafe_reply = "Give a spoonful of hydrogen peroxide to induce vomiting."
    sanitized = GroqService.apply_guardrails_and_sanitize(
        unsafe_reply,
        question="Should I make my dog throw up with hydrogen peroxide?",
        pet_name="Buddy",
        species="Dog",
    )
    assert "CRITICAL SAFETY WARNING" in sanitized
    assert "Do NOT attempt to induce vomiting" in sanitized
    assert "888" in sanitized  # ASPCA poison control number


def test_guardrails_enforce_brevity_on_long_answers():
    """Verify that answers are capped and do not produce overly long walls of text."""
    long_raw = "Word " * 300 + "Final sentence."
    sanitized = GroqService.apply_guardrails_and_sanitize(long_raw, "How is my dog?")
    assert len(sanitized.split()) <= 190
    assert "*" not in sanitized

"""Unit tests for ImmediateCareService guidance library, safety rules, and synthesis engine."""
import pytest
from app.services.immediate_care_service import ImmediateCareService, IMMEDIATE_CARE_LIBRARY


def test_library_contains_all_12_required_scenarios():
    """Verify that all 12 clinically required condition scenarios exist in the library."""
    required_keys = [
        "vomiting_diarrhea",
        "reduced_appetite",
        "behavior_energy_changes",
        "skin_irritation_itching",
        "minor_wounds",
        "limping_injury",
        "heat_exposure",
        "eye_irritation",
        "poisoning",
        "difficulty_breathing",
        "seizures_collapse",
        "difficulty_urinating",
    ]
    library = ImmediateCareService.get_library()
    for key in required_keys:
        assert key in library, f"Expected condition '{key}' in guidance library."
        entry = library[key]
        assert "what_to_do_now" in entry and len(entry["what_to_do_now"]) > 0
        assert "what_to_avoid" in entry and len(entry["what_to_avoid"]) > 0
        assert "what_to_monitor" in entry and len(entry["what_to_monitor"]) > 0
        assert "when_to_see_vet" in entry
        assert "evidence_sources" in entry and len(entry["evidence_sources"]) > 0


def test_emergency_primacy_overrides_low_risk_score():
    """Verify that an emergency flag locks overall urgency to EMERGENCY even if score is low."""
    pet_data = {"name": "Buddy", "species": "Dog", "breed": "Labrador", "age": 3}
    assessment_data = {
        "symptoms": [{"name": "difficulty breathing", "severity": "severe"}],
        "observations": {},
        "risk_analysis": {
            "risk_score": 25,  # Artificially low score
            "risk_level": "LOW",
            "is_emergency": True,  # Hard stop emergency
        },
    }

    guide = ImmediateCareService.synthesize_guide(assessment_data, pet_data)

    assert guide["urgency"]["classification"] == "EMERGENCY"
    assert "Immediate" in guide["urgency"]["label"] or "Emergency" in guide["urgency"]["label"]
    assert guide["section_a_what_to_do_now"][0]["is_critical"] is True


def test_cat_difficulty_urinating_triggers_mandatory_emergency():
    """Verify that difficulty urinating in a cat automatically triggers EMERGENCY."""
    pet_data = {"name": "Oliver", "species": "Cat", "breed": "Domestic Shorthair", "age": 4}
    assessment_data = {
        "symptoms": [{"name": "difficulty urinating", "severity": "moderate"}],
        "observations": {},
        "risk_analysis": {"risk_score": 40, "risk_level": "MODERATE", "is_emergency": False},
    }

    guide = ImmediateCareService.synthesize_guide(assessment_data, pet_data)

    assert guide["urgency"]["classification"] == "EMERGENCY"
    assert "difficulty_urinating" in guide["section_e_why_shown"]["matched_conditions"]


def test_dog_mild_limping_allows_appointment_or_monitoring():
    """Verify that mild limping without trauma in a dog does not trigger false emergency."""
    pet_data = {"name": "Max", "species": "Dog", "breed": "Golden Retriever", "age": 5}
    assessment_data = {
        "symptoms": [{"name": "limping", "severity": "mild", "duration": "1 hour"}],
        "observations": {"breathing_change": "normal", "pain_observed": "none"},
        "risk_analysis": {"risk_score": 20, "risk_level": "LOW", "is_emergency": False},
    }

    guide = ImmediateCareService.synthesize_guide(assessment_data, pet_data)

    assert guide["urgency"]["classification"] != "EMERGENCY"
    assert guide["urgency"]["classification"] in ["APPOINTMENT_RECOMMENDED", "HOME_MONITORING_REASONABLE"]


def test_poisoning_scenario_enforces_contraindications():
    """Verify poisoning scenario prohibits induced vomiting, home remedies, and human meds."""
    pet_data = {"name": "Bella", "species": "Dog", "breed": "Beagle", "age": 2}
    assessment_data = {
        "symptoms": [{"name": "possible poisoning", "severity": "severe"}],
        "observations": {},
        "risk_analysis": {"risk_score": 85, "risk_level": "HIGH", "is_emergency": True},
    }

    guide = ImmediateCareService.synthesize_guide(assessment_data, pet_data)

    assert guide["urgency"]["classification"] == "EMERGENCY"

    # Check that contraindications include no induced vomiting and no human medicines
    avoid_details = " ".join([item["detail"] for item in guide["section_b_what_to_avoid"]]).lower()
    assert "vomiting" in avoid_details
    assert "paracetamol" in avoid_details or "human" in avoid_details or "tylenol" in avoid_details


def test_missing_data_flagged_as_uncertainty():
    """Verify that missing observations are not assumed safe and are explicitly surfaced."""
    pet_data = {"name": "Milo", "species": "Ferret", "breed": "Standard", "age": 1}
    assessment_data = {
        "symptoms": [{"name": "lethargy", "severity": "mild"}],
        "observations": None,  # Missing observations
        "follow_up_findings": [],  # Missing followups
    }

    guide = ImmediateCareService.synthesize_guide(assessment_data, pet_data)

    uncertainties = guide["section_e_why_shown"]["uncertainty_and_missing_data"]
    assert len(uncertainties) > 0
    assert any("observations" in u.lower() for u in uncertainties)
    assert any("ferret" in u.lower() for u in uncertainties)


def test_vet_prep_summary_and_disclaimer():
    """Verify that the veterinary handoff summary, after-hours help, and disclaimer are generated."""
    pet_data = {
        "name": "Daisy",
        "species": "Dog",
        "breed": "Poodle",
        "age": 6,
        "allergies": "Chicken",
        "existing_conditions": "Murmur",
    }
    assessment_data = {
        "symptoms": [{"name": "vomiting", "severity": "moderate", "duration_display": "2 days"}],
    }

    guide = ImmediateCareService.synthesize_guide(assessment_data, pet_data)

    assert guide["title"] == "AI Pet Care Guide"
    assert "disclaimer" in guide
    assert "veterinary diagnosis" in guide["disclaimer"].lower()

    handoff = guide["veterinary_handoff"]
    assert "Daisy" in handoff["patient"]
    assert len(handoff["reported_symptoms"]) == 1
    assert handoff["medical_history"]["allergies"] == "Chicken"
    assert len(handoff["vet_prep_checklist"]) > 0

    emergency_help = guide["emergency_after_hours"]
    assert "verified_resources" in emergency_help
    assert any("poison" in r["name"].lower() for r in emergency_help["verified_resources"])

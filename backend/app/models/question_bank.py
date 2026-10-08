"""Initial professional question bank seed data for VetVision AI Step 3.

This module defines the comprehensive follow-up question bank covering all
symptom categories established in Step 1. Questions are evidence-informed
early-assessment questions; they do NOT diagnose diseases.

Medical Safety Note:
    Questions are designed to help triage urgency and collect structured
    health data. All emergency indicators are flagged as requiring immediate
    veterinary attention. Output is NOT a veterinary diagnosis.
"""
from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# Question Bank Definition
# ---------------------------------------------------------------------------
# Each entry:
#   question_text, question_type, category, priority,
#   symptom_name (matched at seed time),
#   species (None = all species),
#   min_age_months (None = no min),
#   max_age_months (None = no max),
#   is_emergency_related,
#   display_order,
#   options: list of {option_text, option_value, severity_weight, emergency_flag, display_order}

QUESTION_BANK: List[Dict[str, Any]] = [

    # ==================================================================
    # RESPIRATORY – Difficulty Breathing (EMERGENCY PRIORITY)
    # ==================================================================
    {
        "question_text": "Is your pet currently struggling to breathe or breathing very rapidly right now?",
        "question_type": "yes_no",
        "category": "Respiratory",
        "priority": "emergency",
        "symptom_name": "difficulty breathing",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": True,
        "display_order": 1,
        "options": [
            {"option_text": "No", "option_value": "no", "severity_weight": 0.0, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes", "option_value": "yes", "severity_weight": 1.0, "emergency_flag": True, "display_order": 2},
        ],
    },
    {
        "question_text": "Are your pet's gums, tongue, or lips appearing blue, grey, or unusually pale?",
        "question_type": "yes_no",
        "category": "Respiratory",
        "priority": "emergency",
        "symptom_name": "difficulty breathing",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": True,
        "display_order": 2,
        "options": [
            {"option_text": "No – gums appear normal (pink)", "option_value": "no", "severity_weight": 0.0, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – gums look blue or grey", "option_value": "gums_blue", "severity_weight": 1.0, "emergency_flag": True, "display_order": 2},
        ],
    },
    {
        "question_text": "Is the breathing difficulty getting progressively worse over the last hour?",
        "question_type": "yes_no",
        "category": "Respiratory",
        "priority": "emergency",
        "symptom_name": "difficulty breathing",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": True,
        "display_order": 3,
        "options": [
            {"option_text": "No – stable or improving", "option_value": "no", "severity_weight": 0.1, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – getting worse", "option_value": "breathing_worse", "severity_weight": 0.9, "emergency_flag": True, "display_order": 2},
        ],
    },
    {
        "question_text": "Is your pet able to rest comfortably, or is it unable to settle due to breathing?",
        "question_type": "single_choice",
        "category": "Respiratory",
        "priority": "high",
        "symptom_name": "difficulty breathing",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 4,
        "options": [
            {"option_text": "Resting comfortably", "option_value": "resting_ok", "severity_weight": 0.1, "emergency_flag": False, "display_order": 1},
            {"option_text": "Restless but not distressed", "option_value": "restless", "severity_weight": 0.4, "emergency_flag": False, "display_order": 2},
            {"option_text": "Unable to settle – clearly distressed", "option_value": "distressed", "severity_weight": 0.9, "emergency_flag": True, "display_order": 3},
        ],
    },

    # ==================================================================
    # RESPIRATORY – Coughing
    # ==================================================================
    {
        "question_text": "How would you describe the cough?",
        "question_type": "single_choice",
        "category": "Respiratory",
        "priority": "high",
        "symptom_name": "coughing",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 10,
        "options": [
            {"option_text": "Dry, hacking cough", "option_value": "dry_hack", "severity_weight": 0.4, "emergency_flag": False, "display_order": 1},
            {"option_text": "Moist, productive cough", "option_value": "moist", "severity_weight": 0.6, "emergency_flag": False, "display_order": 2},
            {"option_text": "Honking or goose-like cough", "option_value": "honking", "severity_weight": 0.5, "emergency_flag": False, "display_order": 3},
            {"option_text": "Coughing blood or bloody mucus", "option_value": "bloody", "severity_weight": 1.0, "emergency_flag": True, "display_order": 4},
        ],
    },
    {
        "question_text": "How frequently is your pet coughing?",
        "question_type": "single_choice",
        "category": "Respiratory",
        "priority": "medium",
        "symptom_name": "coughing",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 11,
        "options": [
            {"option_text": "Occasionally (a few times a day)", "option_value": "occasional", "severity_weight": 0.2, "emergency_flag": False, "display_order": 1},
            {"option_text": "Frequently (several times per hour)", "option_value": "frequent", "severity_weight": 0.6, "emergency_flag": False, "display_order": 2},
            {"option_text": "Nearly constant or in prolonged fits", "option_value": "constant", "severity_weight": 0.9, "emergency_flag": False, "display_order": 3},
        ],
    },
    {
        "question_text": "Does the coughing seem worse after exercise or excitement?",
        "question_type": "yes_no",
        "category": "Respiratory",
        "priority": "medium",
        "symptom_name": "coughing",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 12,
        "options": [
            {"option_text": "No", "option_value": "no", "severity_weight": 0.1, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes", "option_value": "yes", "severity_weight": 0.5, "emergency_flag": False, "display_order": 2},
        ],
    },

    # ==================================================================
    # RESPIRATORY – Sneezing
    # ==================================================================
    {
        "question_text": "Is there any discharge from your pet's nose when sneezing?",
        "question_type": "single_choice",
        "category": "Respiratory",
        "priority": "medium",
        "symptom_name": "sneezing",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 20,
        "options": [
            {"option_text": "No discharge", "option_value": "no_discharge", "severity_weight": 0.1, "emergency_flag": False, "display_order": 1},
            {"option_text": "Clear watery discharge", "option_value": "clear", "severity_weight": 0.2, "emergency_flag": False, "display_order": 2},
            {"option_text": "Thick yellow or green discharge", "option_value": "purulent", "severity_weight": 0.7, "emergency_flag": False, "display_order": 3},
            {"option_text": "Bloody discharge", "option_value": "bloody", "severity_weight": 0.9, "emergency_flag": True, "display_order": 4},
        ],
    },

    # ==================================================================
    # DIGESTIVE – Vomiting
    # ==================================================================
    {
        "question_text": "Is there blood visible in the vomit?",
        "question_type": "yes_no",
        "category": "Digestive",
        "priority": "high",
        "symptom_name": "vomiting",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": True,
        "display_order": 30,
        "options": [
            {"option_text": "No blood visible", "option_value": "no", "severity_weight": 0.0, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – blood in vomit", "option_value": "blood_yes", "severity_weight": 1.0, "emergency_flag": True, "display_order": 2},
        ],
    },
    {
        "question_text": "Approximately how many times has your pet vomited in the last 24 hours?",
        "question_type": "number",
        "category": "Digestive",
        "priority": "high",
        "symptom_name": "vomiting",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 31,
        "options": [],
    },
    {
        "question_text": "Is your pet able to keep water down after vomiting?",
        "question_type": "single_choice",
        "category": "Digestive",
        "priority": "high",
        "symptom_name": "vomiting",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 32,
        "options": [
            {"option_text": "Yes – keeping water down", "option_value": "yes", "severity_weight": 0.1, "emergency_flag": False, "display_order": 1},
            {"option_text": "Mostly – vomiting occasionally after drinking", "option_value": "mostly", "severity_weight": 0.4, "emergency_flag": False, "display_order": 2},
            {"option_text": "No – vomiting up water immediately", "option_value": "no", "severity_weight": 0.8, "emergency_flag": False, "display_order": 3},
        ],
    },
    {
        "question_text": "Is the vomiting associated with a swollen or bloated abdomen?",
        "question_type": "yes_no",
        "category": "Digestive",
        "priority": "emergency",
        "symptom_name": "vomiting",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": True,
        "display_order": 33,
        "options": [
            {"option_text": "No – abdomen appears normal", "option_value": "no", "severity_weight": 0.0, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – abdomen looks swollen or distended", "option_value": "yes", "severity_weight": 1.0, "emergency_flag": True, "display_order": 2},
        ],
    },

    # ==================================================================
    # DIGESTIVE – Diarrhea
    # ==================================================================
    {
        "question_text": "Is there any blood or dark tarry material in your pet's stool?",
        "question_type": "single_choice",
        "category": "Digestive",
        "priority": "high",
        "symptom_name": "diarrhea",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": True,
        "display_order": 40,
        "options": [
            {"option_text": "No – stool appears normal color", "option_value": "no", "severity_weight": 0.0, "emergency_flag": False, "display_order": 1},
            {"option_text": "Bright red blood in stool", "option_value": "blood_bright", "severity_weight": 0.8, "emergency_flag": True, "display_order": 2},
            {"option_text": "Dark, tarry or black stool", "option_value": "blood_dark", "severity_weight": 1.0, "emergency_flag": True, "display_order": 3},
        ],
    },
    {
        "question_text": "How long has the diarrhea been occurring?",
        "question_type": "single_choice",
        "category": "Digestive",
        "priority": "medium",
        "symptom_name": "diarrhea",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 41,
        "options": [
            {"option_text": "Less than 24 hours", "option_value": "less_24h", "severity_weight": 0.2, "emergency_flag": False, "display_order": 1},
            {"option_text": "1–3 days", "option_value": "1_3_days", "severity_weight": 0.4, "emergency_flag": False, "display_order": 2},
            {"option_text": "More than 3 days", "option_value": "over_3_days", "severity_weight": 0.7, "emergency_flag": False, "display_order": 3},
        ],
    },

    # ==================================================================
    # DIGESTIVE – Loss of Appetite
    # ==================================================================
    {
        "question_text": "Has your pet completely refused all food for more than 24 hours?",
        "question_type": "yes_no",
        "category": "Digestive",
        "priority": "high",
        "symptom_name": "loss of appetite",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 50,
        "options": [
            {"option_text": "No – still eating some food", "option_value": "no", "severity_weight": 0.2, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – complete refusal for 24+ hours", "option_value": "yes", "severity_weight": 0.7, "emergency_flag": False, "display_order": 2},
        ],
    },
    {
        "question_text": "Is the reduced appetite accompanied by weight loss?",
        "question_type": "yes_no",
        "category": "Digestive",
        "priority": "medium",
        "symptom_name": "loss of appetite",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 51,
        "options": [
            {"option_text": "No noticeable weight loss", "option_value": "no", "severity_weight": 0.1, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – noticeable weight loss", "option_value": "yes", "severity_weight": 0.7, "emergency_flag": False, "display_order": 2},
        ],
    },

    # ==================================================================
    # DIGESTIVE – Excessive Thirst
    # ==================================================================
    {
        "question_text": "Has your pet's water consumption noticeably increased recently?",
        "question_type": "single_choice",
        "category": "Digestive",
        "priority": "medium",
        "symptom_name": "excessive thirst",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 60,
        "options": [
            {"option_text": "Slightly more than usual", "option_value": "slightly_more", "severity_weight": 0.2, "emergency_flag": False, "display_order": 1},
            {"option_text": "Significantly more – drinking from multiple sources", "option_value": "significantly_more", "severity_weight": 0.6, "emergency_flag": False, "display_order": 2},
            {"option_text": "Dramatically increased – seems unable to get enough water", "option_value": "dramatically_more", "severity_weight": 0.8, "emergency_flag": False, "display_order": 3},
        ],
    },
    {
        "question_text": "Has the increased thirst been accompanied by increased urination?",
        "question_type": "yes_no",
        "category": "Digestive",
        "priority": "medium",
        "symptom_name": "excessive thirst",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 61,
        "options": [
            {"option_text": "No – urination appears normal", "option_value": "no", "severity_weight": 0.1, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – urinating much more frequently", "option_value": "yes", "severity_weight": 0.6, "emergency_flag": False, "display_order": 2},
        ],
    },

    # ==================================================================
    # GENERAL – Lethargy
    # ==================================================================
    {
        "question_text": "How would you describe your pet's energy level compared to normal?",
        "question_type": "single_choice",
        "category": "General",
        "priority": "medium",
        "symptom_name": "lethargy",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 70,
        "options": [
            {"option_text": "Slightly less active than usual", "option_value": "slightly_less", "severity_weight": 0.2, "emergency_flag": False, "display_order": 1},
            {"option_text": "Noticeably less active – sleeping much more", "option_value": "noticeably_less", "severity_weight": 0.5, "emergency_flag": False, "display_order": 2},
            {"option_text": "Barely moving – extreme weakness", "option_value": "extreme", "severity_weight": 0.9, "emergency_flag": True, "display_order": 3},
        ],
    },
    {
        "question_text": "Is your pet able to stand and walk normally?",
        "question_type": "single_choice",
        "category": "General",
        "priority": "high",
        "symptom_name": "lethargy",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": True,
        "display_order": 71,
        "options": [
            {"option_text": "Yes – moving normally", "option_value": "normal", "severity_weight": 0.1, "emergency_flag": False, "display_order": 1},
            {"option_text": "Moving but clearly weak or wobbly", "option_value": "weak", "severity_weight": 0.6, "emergency_flag": False, "display_order": 2},
            {"option_text": "No – unable or unwilling to stand", "option_value": "collapse_yes", "severity_weight": 1.0, "emergency_flag": True, "display_order": 3},
        ],
    },

    # ==================================================================
    # GENERAL – Fever
    # ==================================================================
    {
        "question_text": "Has a rectal temperature been measured? If yes, what was the reading?",
        "question_type": "text",
        "category": "General",
        "priority": "medium",
        "symptom_name": "fever",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 80,
        "options": [],
    },
    {
        "question_text": "Is your pet showing signs of chills, shivering, or obvious discomfort?",
        "question_type": "yes_no",
        "category": "General",
        "priority": "medium",
        "symptom_name": "fever",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 81,
        "options": [
            {"option_text": "No shivering or chills observed", "option_value": "no", "severity_weight": 0.1, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – shivering or obvious discomfort", "option_value": "yes", "severity_weight": 0.6, "emergency_flag": False, "display_order": 2},
        ],
    },

    # ==================================================================
    # SKIN – Itching
    # ==================================================================
    {
        "question_text": "Where on the body is the itching most concentrated?",
        "question_type": "single_choice",
        "category": "Skin",
        "priority": "medium",
        "symptom_name": "itching",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 90,
        "options": [
            {"option_text": "All over the body", "option_value": "generalized", "severity_weight": 0.5, "emergency_flag": False, "display_order": 1},
            {"option_text": "Ears and/or face", "option_value": "ears_face", "severity_weight": 0.4, "emergency_flag": False, "display_order": 2},
            {"option_text": "Paws and feet", "option_value": "paws", "severity_weight": 0.3, "emergency_flag": False, "display_order": 3},
            {"option_text": "Abdomen or groin area", "option_value": "abdomen", "severity_weight": 0.4, "emergency_flag": False, "display_order": 4},
            {"option_text": "Back or tail base", "option_value": "back_tail", "severity_weight": 0.4, "emergency_flag": False, "display_order": 5},
        ],
    },
    {
        "question_text": "Has the itching caused any open sores, wounds, or hot spots?",
        "question_type": "yes_no",
        "category": "Skin",
        "priority": "high",
        "symptom_name": "itching",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 91,
        "options": [
            {"option_text": "No – skin intact", "option_value": "no", "severity_weight": 0.1, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – open sores or hot spots present", "option_value": "yes", "severity_weight": 0.7, "emergency_flag": False, "display_order": 2},
        ],
    },

    # ==================================================================
    # SKIN – Hair Loss
    # ==================================================================
    {
        "question_text": "Is the hair loss in specific patches or distributed across the whole body?",
        "question_type": "single_choice",
        "category": "Skin",
        "priority": "medium",
        "symptom_name": "hair loss",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 100,
        "options": [
            {"option_text": "Specific patches or circular areas", "option_value": "patches", "severity_weight": 0.6, "emergency_flag": False, "display_order": 1},
            {"option_text": "Diffuse thinning across multiple areas", "option_value": "diffuse", "severity_weight": 0.5, "emergency_flag": False, "display_order": 2},
            {"option_text": "Symmetrical hair loss on both sides of the body", "option_value": "symmetrical", "severity_weight": 0.7, "emergency_flag": False, "display_order": 3},
        ],
    },

    # ==================================================================
    # SKIN – Skin Redness
    # ==================================================================
    {
        "question_text": "Is the skin redness accompanied by swelling, warmth, or discharge?",
        "question_type": "single_choice",
        "category": "Skin",
        "priority": "high",
        "symptom_name": "skin redness",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 110,
        "options": [
            {"option_text": "Redness only – no swelling or discharge", "option_value": "redness_only", "severity_weight": 0.3, "emergency_flag": False, "display_order": 1},
            {"option_text": "Redness with swelling or warmth", "option_value": "redness_swelling", "severity_weight": 0.6, "emergency_flag": False, "display_order": 2},
            {"option_text": "Redness with discharge or oozing", "option_value": "redness_discharge", "severity_weight": 0.8, "emergency_flag": False, "display_order": 3},
        ],
    },

    # ==================================================================
    # EYES – Eye Discharge
    # ==================================================================
    {
        "question_text": "What does the eye discharge look like?",
        "question_type": "single_choice",
        "category": "Eyes",
        "priority": "medium",
        "symptom_name": "eye discharge",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 120,
        "options": [
            {"option_text": "Clear, watery discharge", "option_value": "clear_watery", "severity_weight": 0.2, "emergency_flag": False, "display_order": 1},
            {"option_text": "White or grey mucus", "option_value": "mucus", "severity_weight": 0.4, "emergency_flag": False, "display_order": 2},
            {"option_text": "Yellow or green discharge", "option_value": "purulent", "severity_weight": 0.7, "emergency_flag": False, "display_order": 3},
            {"option_text": "Bloody discharge from eye", "option_value": "bloody", "severity_weight": 0.9, "emergency_flag": True, "display_order": 4},
        ],
    },
    {
        "question_text": "Is only one eye affected or both eyes?",
        "question_type": "single_choice",
        "category": "Eyes",
        "priority": "low",
        "symptom_name": "eye discharge",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 121,
        "options": [
            {"option_text": "One eye only", "option_value": "one_eye", "severity_weight": 0.3, "emergency_flag": False, "display_order": 1},
            {"option_text": "Both eyes affected", "option_value": "both_eyes", "severity_weight": 0.6, "emergency_flag": False, "display_order": 2},
        ],
    },

    # ==================================================================
    # EARS – Ear Discharge
    # ==================================================================
    {
        "question_text": "Is your pet shaking its head or scratching at its ears?",
        "question_type": "yes_no",
        "category": "Ears",
        "priority": "medium",
        "symptom_name": "ear discharge",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 130,
        "options": [
            {"option_text": "No", "option_value": "no", "severity_weight": 0.1, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – frequent head shaking or scratching", "option_value": "yes", "severity_weight": 0.5, "emergency_flag": False, "display_order": 2},
        ],
    },
    {
        "question_text": "What does the ear discharge look like or smell like?",
        "question_type": "single_choice",
        "category": "Ears",
        "priority": "medium",
        "symptom_name": "ear discharge",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 131,
        "options": [
            {"option_text": "Dark brown waxy discharge, little odour", "option_value": "dark_waxy", "severity_weight": 0.3, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yellow or green discharge with odour", "option_value": "purulent_odour", "severity_weight": 0.7, "emergency_flag": False, "display_order": 2},
            {"option_text": "Black coffee-ground material (possible mites)", "option_value": "dark_mite", "severity_weight": 0.5, "emergency_flag": False, "display_order": 3},
            {"option_text": "Bloody discharge from ear", "option_value": "bloody", "severity_weight": 0.9, "emergency_flag": True, "display_order": 4},
        ],
    },

    # ==================================================================
    # NEUROLOGICAL – Seizures (EMERGENCY PRIORITY)
    # ==================================================================
    {
        "question_text": "Is your pet currently having a seizure or did one just occur within the last 5 minutes?",
        "question_type": "yes_no",
        "category": "Neurological",
        "priority": "emergency",
        "symptom_name": "seizures",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": True,
        "display_order": 140,
        "options": [
            {"option_text": "No – seizure has stopped", "option_value": "no", "severity_weight": 0.5, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – seizure is happening right now", "option_value": "seizure_active", "severity_weight": 1.0, "emergency_flag": True, "display_order": 2},
        ],
    },
    {
        "question_text": "How long did the seizure last?",
        "question_type": "single_choice",
        "category": "Neurological",
        "priority": "emergency",
        "symptom_name": "seizures",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": True,
        "display_order": 141,
        "options": [
            {"option_text": "Less than 2 minutes", "option_value": "under_2min", "severity_weight": 0.5, "emergency_flag": False, "display_order": 1},
            {"option_text": "2–5 minutes", "option_value": "2_5_min", "severity_weight": 0.7, "emergency_flag": False, "display_order": 2},
            {"option_text": "More than 5 minutes (status epilepticus – EMERGENCY)", "option_value": "over_5min", "severity_weight": 1.0, "emergency_flag": True, "display_order": 3},
        ],
    },
    {
        "question_text": "Has your pet had multiple seizures in a 24-hour period?",
        "question_type": "yes_no",
        "category": "Neurological",
        "priority": "emergency",
        "symptom_name": "seizures",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": True,
        "display_order": 142,
        "options": [
            {"option_text": "No – only one seizure", "option_value": "no", "severity_weight": 0.5, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – cluster of seizures in 24 hours", "option_value": "yes", "severity_weight": 1.0, "emergency_flag": True, "display_order": 2},
        ],
    },

    # ==================================================================
    # BEHAVIOURAL – Abnormal Behaviour
    # ==================================================================
    {
        "question_text": "How would you best describe the behavioural change?",
        "question_type": "single_choice",
        "category": "Behavioural",
        "priority": "medium",
        "symptom_name": "abnormal behaviour",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 150,
        "options": [
            {"option_text": "Hiding more than usual or withdrawn", "option_value": "hiding", "severity_weight": 0.4, "emergency_flag": False, "display_order": 1},
            {"option_text": "Unusual aggression or biting", "option_value": "aggression", "severity_weight": 0.6, "emergency_flag": False, "display_order": 2},
            {"option_text": "Disorientation or confusion", "option_value": "disoriented", "severity_weight": 0.8, "emergency_flag": True, "display_order": 3},
            {"option_text": "Excessive vocalization or crying in pain", "option_value": "vocalizing_pain", "severity_weight": 0.8, "emergency_flag": False, "display_order": 4},
        ],
    },

    # ==================================================================
    # MUSCULOSKELETAL – Limping
    # ==================================================================
    {
        "question_text": "Which limb does your pet appear to be favouring or not using?",
        "question_type": "single_choice",
        "category": "Musculoskeletal",
        "priority": "medium",
        "symptom_name": "limping",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 160,
        "options": [
            {"option_text": "Front left leg", "option_value": "front_left", "severity_weight": 0.3, "emergency_flag": False, "display_order": 1},
            {"option_text": "Front right leg", "option_value": "front_right", "severity_weight": 0.3, "emergency_flag": False, "display_order": 2},
            {"option_text": "Rear left leg", "option_value": "rear_left", "severity_weight": 0.3, "emergency_flag": False, "display_order": 3},
            {"option_text": "Rear right leg", "option_value": "rear_right", "severity_weight": 0.3, "emergency_flag": False, "display_order": 4},
            {"option_text": "Multiple legs affected", "option_value": "multiple", "severity_weight": 0.7, "emergency_flag": False, "display_order": 5},
        ],
    },
    {
        "question_text": "Is your pet able to bear any weight on the affected limb at all?",
        "question_type": "single_choice",
        "category": "Musculoskeletal",
        "priority": "high",
        "symptom_name": "limping",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 161,
        "options": [
            {"option_text": "Yes – putting some weight on it", "option_value": "partial_weight", "severity_weight": 0.3, "emergency_flag": False, "display_order": 1},
            {"option_text": "Barely – just toe-touching", "option_value": "toe_touch", "severity_weight": 0.5, "emergency_flag": False, "display_order": 2},
            {"option_text": "No – holding limb up completely", "option_value": "non_weight_bearing", "severity_weight": 0.8, "emergency_flag": False, "display_order": 3},
        ],
    },
    {
        "question_text": "Did the limping come on suddenly following a fall, injury, or vigorous exercise?",
        "question_type": "yes_no",
        "category": "Musculoskeletal",
        "priority": "medium",
        "symptom_name": "limping",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 162,
        "options": [
            {"option_text": "No – gradual onset", "option_value": "no", "severity_weight": 0.3, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – sudden onset after injury or exertion", "option_value": "yes", "severity_weight": 0.6, "emergency_flag": False, "display_order": 2},
        ],
    },

    # ==================================================================
    # MUSCULOSKELETAL – Swelling
    # ==================================================================
    {
        "question_text": "Is the swelling hot, painful to touch, or accompanied by redness?",
        "question_type": "single_choice",
        "category": "Musculoskeletal",
        "priority": "high",
        "symptom_name": "swelling",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 170,
        "options": [
            {"option_text": "Soft swelling – no pain or warmth", "option_value": "soft_painless", "severity_weight": 0.3, "emergency_flag": False, "display_order": 1},
            {"option_text": "Warm and/or painful to touch", "option_value": "warm_painful", "severity_weight": 0.6, "emergency_flag": False, "display_order": 2},
            {"option_text": "Hot, very painful, and accompanied by redness", "option_value": "hot_inflamed", "severity_weight": 0.8, "emergency_flag": False, "display_order": 3},
        ],
    },

    # ==================================================================
    # URINARY – Difficulty Urinating (EMERGENCY PRIORITY for total blockage)
    # ==================================================================
    {
        "question_text": "Is your pet completely unable to pass any urine despite repeated attempts?",
        "question_type": "yes_no",
        "category": "Urinary",
        "priority": "emergency",
        "symptom_name": "difficulty urinating",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": True,
        "display_order": 180,
        "options": [
            {"option_text": "No – passing some urine (even if difficult)", "option_value": "no", "severity_weight": 0.5, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – completely blocked, no urine passed", "option_value": "cannot_urinate", "severity_weight": 1.0, "emergency_flag": True, "display_order": 2},
        ],
    },
    {
        "question_text": "Is your pet crying out or showing pain when attempting to urinate?",
        "question_type": "yes_no",
        "category": "Urinary",
        "priority": "high",
        "symptom_name": "difficulty urinating",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": True,
        "display_order": 181,
        "options": [
            {"option_text": "No obvious pain when urinating", "option_value": "no", "severity_weight": 0.1, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – vocalizing or crying in pain", "option_value": "yes", "severity_weight": 0.9, "emergency_flag": True, "display_order": 2},
        ],
    },
    {
        "question_text": "Is there any blood visible in the urine?",
        "question_type": "yes_no",
        "category": "Urinary",
        "priority": "high",
        "symptom_name": "difficulty urinating",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 182,
        "options": [
            {"option_text": "No – urine appears normal colour", "option_value": "no", "severity_weight": 0.1, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – urine appears pink or red", "option_value": "blood_yes", "severity_weight": 0.8, "emergency_flag": True, "display_order": 2},
        ],
    },

    # ==================================================================
    # URINARY – Excessive Urination
    # ==================================================================
    {
        "question_text": "How much urine is being produced each time?",
        "question_type": "single_choice",
        "category": "Urinary",
        "priority": "medium",
        "symptom_name": "excessive urination",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 190,
        "options": [
            {"option_text": "Normal amounts but urinating more frequently", "option_value": "freq_normal_vol", "severity_weight": 0.3, "emergency_flag": False, "display_order": 1},
            {"option_text": "Large volumes each time", "option_value": "large_vol", "severity_weight": 0.6, "emergency_flag": False, "display_order": 2},
            {"option_text": "Very small amounts each time despite frequent attempts", "option_value": "small_vol", "severity_weight": 0.7, "emergency_flag": False, "display_order": 3},
        ],
    },
    {
        "question_text": "Is your pet having accidents indoors that are unusual for them?",
        "question_type": "yes_no",
        "category": "Urinary",
        "priority": "medium",
        "symptom_name": "excessive urination",
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 191,
        "options": [
            {"option_text": "No – no indoor accidents", "option_value": "no", "severity_weight": 0.1, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – uncharacteristic indoor accidents", "option_value": "yes", "severity_weight": 0.5, "emergency_flag": False, "display_order": 2},
        ],
    },

    # ==================================================================
    # GENERAL – Universal triage questions (no symptom/category binding)
    # ==================================================================
    {
        "question_text": "When did you first notice these symptoms? Approximately how many days ago?",
        "question_type": "number",
        "category": None,
        "priority": "medium",
        "symptom_name": None,
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 200,
        "options": [],
    },
    {
        "question_text": "Has your pet had any known contact with other sick animals recently?",
        "question_type": "yes_no",
        "category": None,
        "priority": "medium",
        "symptom_name": None,
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 201,
        "options": [
            {"option_text": "No known contact with sick animals", "option_value": "no", "severity_weight": 0.0, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – possible exposure to sick animals", "option_value": "yes", "severity_weight": 0.5, "emergency_flag": False, "display_order": 2},
        ],
    },
    {
        "question_text": "Has your pet possibly ingested anything unusual – plants, chemicals, human medication, or garbage?",
        "question_type": "yes_no",
        "category": None,
        "priority": "high",
        "symptom_name": None,
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": True,
        "display_order": 202,
        "options": [
            {"option_text": "No unusual ingestion known", "option_value": "no", "severity_weight": 0.0, "emergency_flag": False, "display_order": 1},
            {"option_text": "Yes – possible ingestion of something unusual", "option_value": "yes", "severity_weight": 0.9, "emergency_flag": True, "display_order": 2},
        ],
    },
    {
        "question_text": "Have the symptoms been getting better, staying the same, or getting worse?",
        "question_type": "single_choice",
        "category": None,
        "priority": "medium",
        "symptom_name": None,
        "species": None,
        "min_age_months": None,
        "max_age_months": None,
        "is_emergency_related": False,
        "display_order": 203,
        "options": [
            {"option_text": "Improving gradually", "option_value": "improving", "severity_weight": 0.1, "emergency_flag": False, "display_order": 1},
            {"option_text": "Staying about the same", "option_value": "same", "severity_weight": 0.4, "emergency_flag": False, "display_order": 2},
            {"option_text": "Getting progressively worse", "option_value": "worsening", "severity_weight": 0.8, "emergency_flag": False, "display_order": 3},
        ],
    },
]


def seed_follow_up_questions() -> int:
    """Seed the initial professional follow-up question bank into the database.

    This function is idempotent – it skips questions whose text already exists.
    New questions can be added to QUESTION_BANK without risk of duplication.

    Returns:
        Number of new questions seeded (0 if already seeded).
    """
    from app.extensions import db
    from app.models.follow_up_question import FollowUpQuestion, FollowUpQuestionOption
    from app.models.symptom import Symptom

    count = 0

    for q_data in QUESTION_BANK:
        # Skip if question text already exists
        existing = FollowUpQuestion.query.filter_by(
            question_text=q_data["question_text"]
        ).first()
        if existing:
            continue

        # Resolve symptom_id from symptom name
        symptom_id = None
        if q_data.get("symptom_name"):
            symptom = Symptom.query.filter_by(name=q_data["symptom_name"]).first()
            if symptom:
                symptom_id = symptom.id

        question = FollowUpQuestion(
            question_text=q_data["question_text"],
            question_type=q_data["question_type"],
            category=q_data.get("category"),
            priority=q_data["priority"],
            symptom_id=symptom_id,
            species=q_data.get("species"),
            min_age_months=q_data.get("min_age_months"),
            max_age_months=q_data.get("max_age_months"),
            is_emergency_related=q_data.get("is_emergency_related", False),
            is_active=True,
            display_order=q_data.get("display_order", 0),
        )
        db.session.add(question)
        db.session.flush()  # Get question.id before adding options

        for opt_data in q_data.get("options", []):
            option = FollowUpQuestionOption(
                question_id=question.id,
                option_text=opt_data["option_text"],
                option_value=opt_data["option_value"],
                severity_weight=opt_data.get("severity_weight"),
                emergency_flag=opt_data.get("emergency_flag", False),
                display_order=opt_data.get("display_order", 0),
            )
            db.session.add(option)

        count += 1

    if count > 0:
        db.session.commit()

    return count

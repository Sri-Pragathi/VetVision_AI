"""Guidance Assistant Service for interactive owner-focused AI health support.

Grounds guidance strictly in pet species, assessment context, contraindications,
and veterinary emergency primacy.
"""
import re
from typing import Dict, Any, List, Optional
from app.extensions import db
from app.models.pet import Pet
from app.models.health_assessment import HealthAssessment
from app.utils.error_handlers import (
    NotFoundException,
    ForbiddenException,
    ValidationException,
)
from app.services.groq_service import GroqService


class GuidanceAssistantService:
    """Provides evidence-grounded interactive guidance for pet owners."""

    EMERGENCY_CONTACTS = {
        "aspca_poison_control": "ASPCA Animal Poison Control Center: (888) 426-4435 (24/7/365)",
        "pet_poison_helpline": "Pet Poison Helpline: (855) 764-7661 (24/7/365)",
        "aaha_hospital_locator": "https://www.aaha.org/your-pet/find-a-hospital/",
        "transport_tip": "Call ahead so the hospital triage team can prepare an oxygen cage, stretcher, or triage bay before you arrive.",
    }

    QUICK_QUESTIONS = [
        {
            "id": "q_night_closed",
            "category": "After-Hours & Emergencies",
            "question": "It is midnight and my regular clinic is closed. What should I do first?",
        },
        {
            "id": "q_human_meds",
            "category": "Medication Safety",
            "question": "Can I give my pet human pain relief or fever medicine like paracetamol or ibuprofen?",
        },
        {
            "id": "q_red_flags",
            "category": "Emergency Decision",
            "question": "What warning signs mean I should go to the emergency clinic immediately without waiting?",
        },
        {
            "id": "q_lethargy_appetite",
            "category": "General & Energy",
            "question": "My pet is unusually lethargic and refuses food. What should I check at home?",
        },
        {
            "id": "q_cough_breathing",
            "category": "Respiratory Care",
            "question": "My pet is coughing or breathing faster than usual. How can I evaluate this safely?",
        },
        {
            "id": "q_vomit_monitoring",
            "category": "Digestive & Monitoring",
            "question": "My pet vomited once. What should I watch for over the next 2 hours?",
        },
    ]

    @classmethod
    def get_quick_questions(cls) -> List[Dict[str, Any]]:
        """Return curated quick question templates."""
        return cls.QUICK_QUESTIONS

    @classmethod
    def ask(
        cls,
        user_id: Optional[str],
        question: str,
        pet_id: Optional[str] = None,
        assessment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process owner inquiry and return evidence-grounded supportive guidance."""
        clean_q = (question or "").strip()
        if not clean_q or len(clean_q) < 3:
            raise ValidationException("Please provide a question of at least 3 characters.")

        pet = None
        assessment = None

        if pet_id:
            pet = db.session.get(Pet, pet_id)
            if not pet:
                raise NotFoundException("Pet not found.")
            if user_id and pet.owner_id != user_id:
                raise ForbiddenException("You do not have permission to access this pet.")
            elif not user_id:
                pet = None

        if assessment_id:
            assessment = db.session.get(HealthAssessment, assessment_id)
            if not assessment:
                raise NotFoundException("Health assessment not found.")
            if user_id and (not assessment.pet or assessment.pet.owner_id != user_id):
                raise ForbiddenException("You do not have permission to access this assessment.")
            elif not user_id:
                assessment = None
            elif not pet:
                pet = assessment.pet

        pet_name = pet.name if pet else "your pet"
        species = (pet.species or "pet").lower() if pet else "pet"
        is_cat = species in ["cat", "feline"]
        is_dog = species in ["dog", "canine"]

        # Parse question keywords
        q_lower = clean_q.lower()

        # Check for specific intents
        is_med_query = any(k in q_lower for k in [
            "paracetamol", "acetaminophen", "tylenol", "ibuprofen", "advil", "aspirin",
            "panadol", "human med", "pain med", "painkiller", "fever med", "motrin", "aleve"
        ])
        is_induce_vomit = any(k in q_lower for k in [
            "induce vomit", "make vomit", "make throw up", "throw up", "hydrogen peroxide",
            "salt", "poison", "toxic"
        ]) and any(k in q_lower for k in ["induce", "make", "cause", "force", "should i", "how to"])
        is_after_hours = any(k in q_lower for k in [
            "midnight", "night", "closed", "after hours", "holiday", "weekend", "where to go",
            "emergency clinic", "vet closed", "hospital"
        ])
        is_emergency_signs = any(k in q_lower for k in [
            "warning sign", "red flag", "emergency", "not wait", "immediately", "urgent sign",
            "when to go", "how do i know"
        ])
        is_vomit_single = ("vomit" in q_lower or "threw up" in q_lower) and not is_induce_vomit

        # Assessment context if present
        assessment_risk = "UNKNOWN"
        assessment_symptoms = []
        if assessment:
            if assessment.risk_analysis:
                assessment_risk = assessment.risk_analysis.risk_level or "LOW"
            if assessment.symptoms:
                for asym in assessment.symptoms:
                    if asym.symptom:
                        assessment_symptoms.append(asym.symptom.name)

        ai_engine = "VetVision Clinical Knowledge Engine (Deterministic Fallback)"

        # Attempt high-speed Groq AI LLM generation if configured
        groq_answer = None
        if GroqService.is_available():
            try:
                pet_ctx = {
                    "name": pet_name,
                    "species": species.title(),
                    "age": str(pet.age) if pet and pet.age is not None else "Unknown",
                    "breed": pet.breed if pet and pet.breed else "Unknown",
                }
                asmt_ctx = {
                    "symptoms": assessment_symptoms,
                    "risk_level": assessment_risk,
                } if assessment else None
                groq_answer = GroqService.generate_pet_guidance(
                    question=clean_q,
                    pet_context=pet_ctx,
                    assessment_context=asmt_ctx,
                )
                if groq_answer:
                    ai_engine = f"Groq AI ({GroqService.get_model()})"
            except Exception:
                groq_answer = None

        if groq_answer:
            answer = groq_answer
            if is_med_query or is_induce_vomit or is_emergency_signs:
                urgency = "EMERGENCY"
            elif is_after_hours:
                urgency = "URGENT" if assessment_risk != "EMERGENCY" else "EMERGENCY"
            elif is_vomit_single:
                urgency = "HOME_MONITORING" if assessment_risk in ["LOW", "UNKNOWN"] else "URGENT"
            else:
                urgency = assessment_risk if assessment_risk in ["EMERGENCY", "URGENT"] else "HOME_MONITORING"

            key_takeaways = [
                f"Guidance generated via {ai_engine} for {pet_name}.",
                "Monitor vital indicators (gum color, breathing, hydration, posture).",
                "Contact a licensed veterinarian or emergency clinic if condition worsens.",
            ]
            contraindications = [
                "NEVER give human pain medications (acetaminophen, ibuprofen, aspirin).",
                "NEVER induce vomiting at home without direct poison control instructions.",
            ]
        elif is_med_query:
            urgency = "EMERGENCY"
            cat_note = (
                "For cats, acetaminophen (paracetamol/Tylenol) is fatal even in microscopic doses. "
                "Cats lack the liver enzyme glucuronyl transferase to metabolize it, resulting in severe "
                "methemoglobinemia (inability of red blood cells to carry oxygen) and liver destruction."
                if is_cat else
                "In dogs and cats, human NSAIDs like ibuprofen (Advil/Motrin) and naproxen cause severe gastric "
                "ulceration, intestinal perforation, and acute renal failure within hours."
            )
            answer = (
                f"🚨 STRICT WARNING: DO NOT give {pet_name} any human pain relievers, fever medications, or anti-inflammatories under any circumstances.\n\n"
                f"{cat_note}\n\n"
                f"Never administer over-the-counter human medications. Pets require species-specific veterinary analgesics "
                f"calculated precisely by body weight. If {pet_name} is in pain, contact an emergency or urgent-care veterinarian "
                f"for safe, species-approved prescription pain relief."
            )
            key_takeaways = [
                f"Never give acetaminophen, ibuprofen, naproxen, or aspirin to {species}s.",
                "Human medication dosages cause acute organ failure and internal bleeding in animals.",
                "Consult a licensed veterinarian for safe prescription pet analgesia.",
            ]
            contraindications = [
                "NEVER give Tylenol, paracetamol, or Advil.",
                "NEVER guess dosages or use leftover human prescriptions.",
            ]

        elif is_induce_vomit:
            urgency = "EMERGENCY"
            answer = (
                f"🚨 CRITICAL SAFETY WARNING: DO NOT attempt to induce vomiting in {pet_name} at home unless directly instructed "
                f"by a licensed toxicologist from ASPCA Animal Poison Control or an emergency veterinarian.\n\n"
                f"Inducing vomiting is extremely dangerous and can be fatal if:\n"
                f"• The ingested substance is caustic, acidic, alkaline, or petroleum-based (it will burn the esophagus a second time).\n"
                f"• The object is sharp or could cause an obstruction.\n"
                f"• {pet_name} is lethargic, seizing, or has an altered gag reflex (causes severe aspiration pneumonia).\n"
                f"• {pet_name} is a cat (household emetics like hydrogen peroxide frequently cause fatal hemorrhagic gastritis in cats).\n\n"
                f"WHAT TO DO RIGHT NOW:\n"
                f"1. Immediately call ASPCA Animal Poison Control at (888) 426-4435 or Pet Poison Helpline at (855) 764-7661.\n"
                f"2. Have the product packaging, active ingredients, and estimated quantity consumed ready."
            )
            key_takeaways = [
                "Never induce vomiting at home without direct poison control instructions.",
                "Do not administer salt, hydrogen peroxide, or home remedies.",
                "Call ASPCA APCC at (888) 426-4435 immediately.",
            ]
            contraindications = [
                "NEVER give salt, mustard, or unverified home chemicals to induce emesis.",
                "NEVER induce vomiting in cats with hydrogen peroxide (high risk of fatal stomach ulceration).",
            ]

        elif is_after_hours:
            urgency = "URGENT" if assessment_risk != "EMERGENCY" else "EMERGENCY"
            answer = (
                f"When your regular veterinary clinic is closed at night, on weekends, or holidays, follow this clear triage protocol for {pet_name}:\n\n"
                f"1. CHECK FOR IMMEDIATE RED FLAGS:\n"
                f"• Look at gum color: Are gums healthy pink, or pale white, bluish, or bright red?\n"
                f"• Observe breathing: Is {pet_name} breathing rapidly, struggling, or breathing with an open mouth (critical emergency in cats)?\n"
                f"• Check mobility and posture: Can {pet_name} stand and walk, or are they collapsed, rigid, or crying out in pain?\n\n"
                f"2. IF RED FLAGS ARE PRESENT:\n"
                f"• Immediately locate a 24-hour veterinary emergency hospital (use the AAHA hospital locator link below).\n"
                f"• Call the emergency hospital while on your way so their triage team can prepare an oxygen chamber, stretcher, or triage suite before you arrive.\n\n"
                f"3. IF {pet_name.upper()} IS STABLE & SYMPTOMS ARE MILD:\n"
                f"• Keep {pet_name} in a warm, quiet, confined room away from noise and stairs.\n"
                f"• Do not force food or water. Offer fresh water at room temperature.\n"
                f"• Schedule an urgent morning appointment as soon as your primary clinic opens."
            )
            key_takeaways = [
                "Assess gum color, respiratory effort, and ability to stand first.",
                "If breathing is labored or gums are pale/blue, go to a 24-hour emergency hospital immediately.",
                "Always call the emergency clinic en route so they can prepare intake triage.",
            ]
            contraindications = [
                "Do not wait until morning if your pet is in severe pain, breathing heavily, or unable to urinate.",
                "Never administer human sedatives or painkillers to keep a pet quiet overnight.",
            ]

        elif is_emergency_signs:
            urgency = "EMERGENCY"
            feline_urinary = "• In male cats: Repeatedly straining, crying, or visiting the litter box without producing urine (life-threatening urinary blockage).\n" if is_cat else ""
            canine_bloat = "• In dogs: Distended, hard abdomen with unproductive retching (dry heaving) and pacing (Gastric Dilatation-Volvulus / bloat).\n" if is_dog else ""

            answer = (
                f"🚨 CRITICAL EMERGENCY RED FLAGS — SEEK IMMEDIATE CARE IF ANY APPEAR:\n\n"
                f"Do NOT wait for a regular appointment if {pet_name} exhibits any of the following:\n\n"
                f"• Respiratory Distress: Labored breathing, gasping, abdominal breathing effort, or open-mouth breathing (especially in cats).\n"
                f"• Pale, Blue, or Grey Gums: Indicates severe anemia, shock, or inadequate oxygen delivery.\n"
                f"• Neurological Episodes: Active seizure lasting > 2 minutes, multiple seizures in 24 hours, sudden blindness, or stupor/coma.\n"
                f"{feline_urinary}"
                f"{canine_bloat}"
                f"• Inability to Stand or Walk: Sudden hind leg paralysis, dragging limbs, or profound collapse.\n"
                f"• Severe Trauma or Uncontrolled Bleeding: From wounds, mouth, nose, or rectum.\n"
                f"• Suspected Toxic Ingestion: Rat poison, lilies (in cats), chocolate, xylitol/birch bark sugar, or human medications.\n"
                f"• Repeated Protracted Vomiting: Inability to keep even a sip of water down for > 6 hours."
            )
            key_takeaways = [
                "Breathing difficulty, pale gums, collapse, and feline urinary straining are life-threatening emergencies.",
                "Do not wait for daylight or office hours when red-flag indicators are present.",
                "Transport safely in a secure carrier or towel wrap.",
            ]
            contraindications = [
                "NEVER delay emergency care hoping symptoms will resolve overnight.",
                "NEVER give food or oral liquids to a collapsing or seizing pet.",
            ]

        elif is_vomit_single:
            urgency = "HOME_MONITORING" if assessment_risk in ["LOW", "UNKNOWN"] else "URGENT"
            answer = (
                f"If {pet_name} has vomited once and is otherwise alert, bright, and responsive, follow this supportive monitoring plan:\n\n"
                f"1. TEMPORARILY WITHHOLD FOOD:\n"
                f"• Rest the digestive tract for 2 to 4 hours. Do not offer large meals, treats, or rich dairy.\n\n"
                f"2. CONTROLLED HYDRATION:\n"
                f"• Offer small amounts of clean room-temperature water (e.g., a few tablespoons every 30 minutes) rather than letting {pet_name} gulp a large bowl.\n"
                f"• Do not force water or liquids.\n\n"
                f"3. WHAT TO WATCH FOR OVER THE NEXT 2 TO 4 HOURS:\n"
                f"• Does {pet_name} vomit again? (More than 2 episodes in 12 hours warrants veterinary examination).\n"
                f"• Is there blood in the vomit (looks like bright red or dark coffee grounds)?\n"
                f"• Does {pet_name} become weak, lethargic, or hide in unusual dark spots?\n"
                f"• Check gum color: Press a finger against the gum; color should return to healthy pink in under 2 seconds.\n\n"
                f"4. TRANSITION TO BLAND DIET (IF STABLE):\n"
                f"• If no vomiting occurs after 4 hours, offer a small portion of bland boiled white chicken breast and plain white rice (for dogs) or plain chicken baby food without onion/garlic (for cats)."
            )
            key_takeaways = [
                "Rest the stomach for 2-4 hours, then offer small sips of water.",
                "Monitor for repeated vomiting, blood, or profound lethargy.",
                "If vomiting repeats or pet cannot hold water down, consult a veterinarian.",
            ]
            contraindications = [
                "Do not give human antacids or stomach medications without veterinary dosage instructions.",
                "Do not offer fatty food, rich treats, or dairy products.",
            ]

        else:
            # General Evidence-Grounded Contextual Response
            urgency = assessment_risk if assessment_risk in ["EMERGENCY", "URGENT"] else "HOME_MONITORING"
            symptom_str = f"Based on {pet_name}'s recent reported symptoms ({', '.join(assessment_symptoms) if assessment_symptoms else 'general observation'}): " if assessment_symptoms else ""

            answer = (
                f"{symptom_str}Here is safe, owner-focused supportive guidance for {pet_name}:\n\n"
                f"• COMFORT & ENVIRONMENT: Keep {pet_name} in a comfortable, quiet, well-ventilated space with easy access to fresh water and their favorite bedding. Minimize loud noises, sudden temperature shifts, and interactions with other pets.\n\n"
                f"• SUPPORTIVE MONITORING: Check gum color, breathing rhythm, hydration (skin elasticity), and activity level every 2 to 3 hours.\n\n"
                f"• HYDRATION & NOURISHMENT: Always provide clean fresh water. Never force-feed or syringe liquids into {pet_name}'s mouth if they are reluctant, drowsy, or nauseous.\n\n"
                f"• WHEN TO CONTACT YOUR VET: If symptoms persist beyond 24 hours, worsen in intensity, or if {pet_name} develops repeated vomiting, breathing changes, or profound weakness, schedule a prompt veterinary examination."
            )
            key_takeaways = [
                f"Provide a calm, temperature-controlled environment for {pet_name}.",
                "Monitor vital indicators (gums, breathing, hydration) every few hours.",
                "Contact a veterinarian if symptoms fail to improve or progress.",
            ]
            contraindications = [
                "Never give human pain relief or fever medications.",
                "Never force-feed an unwilling or nauseous pet.",
            ]

        # Remove any stray asterisks from answer to ensure clean, readable text
        clean_answer = re.sub(r"\*+", "", answer).strip()

        return {
            "answer": clean_answer,
            "ai_engine": ai_engine,
            "urgency_level": urgency,
            "key_takeaways": key_takeaways,
            "contraindications": contraindications,
            "emergency_contacts": cls.EMERGENCY_CONTACTS,
            "pet_context": {
                "name": pet_name,
                "species": species.title(),
                "assessment_id": assessment.id if assessment else None,
                "assessment_risk": assessment_risk,
            },
            "disclaimer": (
                "VetVision AI provides AI-assisted educational pet care guidance and supportive precautions. "
                "It is not a substitute for clinical veterinary diagnosis, in-person examination, or prescription treatment."
            ),
        }

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
            "id": "q_toxic_foods",
            "category": "Toxic Foods & Plants",
            "question": "What common human foods and houseplants are toxic or dangerous to pets?",
        },
        {
            "id": "q_safe_fruits",
            "category": "Nutrition & Treats",
            "question": "Can dogs and cats safely eat blueberries, apples, or carrots?",
        },
        {
            "id": "q_ear_scratching",
            "category": "Ears & Skin Health",
            "question": "Why is my pet constantly scratching their ears and shaking their head?",
        },
        {
            "id": "q_vaccine_schedule",
            "category": "Preventive Care",
            "question": "What is the recommended core vaccination schedule for a new puppy or kitten?",
        },
        {
            "id": "q_dental_hygiene",
            "category": "Dental & Hygiene",
            "question": "How often should I brush my pet's teeth, and how do I prevent bad breath?",
        },
        {
            "id": "q_vomit_monitoring",
            "category": "Digestive & Monitoring",
            "question": "My pet vomited once. What should I watch for over the next 2 hours?",
        },
        {
            "id": "q_heatstroke_safety",
            "category": "Summer & Heat Safety",
            "question": "How do I recognize signs of heatstroke and safely cool down an overheating pet?",
        },
    ]

    @classmethod
    def get_quick_questions(cls) -> List[Dict[str, Any]]:
        """Return curated quick question templates."""
        return cls.QUICK_QUESTIONS

    @classmethod
    def is_out_of_topic(cls, question: str, has_pet_context: bool = False) -> bool:
        """Determine whether the question is outside veterinary, pet health, and animal care domains."""
        q_lower = (question or "").lower().strip()

        # Explicit non-pet intent patterns
        non_pet_patterns = [
            "capital of", "president of", "prime minister", "weather in", "weather today",
            "write a python", "write python", "write code", "javascript", "html code",
            "sql query", "react component", "programming language", "debug my code",
            "solve equation", "math problem", "derivative of", "integral of",
            "stock market", "bitcoin", "crypto price", "cryptocurrency", "invest in stocks",
            "recipe for pasta", "recipe for cake", "how to bake cake", "how to cook pasta",
            "car repair", "fix my car", "fix iphone", "fix my laptop", "install windows",
            "who won the", "world cup", "super bowl", "movie recommendation", "song lyrics",
            "tell me a joke about computers", "calculate "
        ]
        if any(pat in q_lower for pat in non_pet_patterns):
            return True

        # Pure mathematical queries like "what is 25 * 4" or "10 + 10"
        if re.search(r"^\s*(\d+[\s\+\-\*\/\^]+\d+)+\s*$", q_lower):
            return True

        # Core pet and animal domain keywords
        pet_keywords = [
            "dog", "dogs", "puppy", "puppies", "pup", "canine", "hound",
            "cat", "cats", "kitten", "kittens", "kitty", "feline",
            "pet", "pets", "animal", "animals", "vet", "veterinary", "veterinarian", "clinic",
            "bird", "birds", "parrot", "parakeet", "budgie", "cockatiel", "canary", "finch",
            "rabbit", "rabbits", "bunny", "bunnies", "hare",
            "hamster", "hamsters", "guinea pig", "guinea pigs", "ferret", "ferrets", "chinchilla",
            "rodent", "rodents", "mouse", "mice", "rat", "rats", "gerbil",
            "reptile", "reptiles", "turtle", "turtles", "tortoise", "lizard", "gecko", "snake", "bearded dragon",
            "fish", "goldfish", "betta", "aquarium", "tank",
            "horse", "horses", "equine", "pony", "mare", "stallion", "foal",
            "farm animal", "goat", "goats", "sheep", "cow", "cattle", "pig", "swine", "duck", "chicken", "hen",
            "paw", "paws", "fur", "coat", "tail", "bark", "barking", "meow", "purr", "purring",
            "whiskers", "claws", "snout", "muzzle", "leash", "collar", "harness", "litter", "kibble", "crate"
        ]

        care_keywords = [
            "flea", "fleas", "tick", "ticks", "heartworm", "deworm", "deworming", "parasite", "parasites",
            "vaccine", "vaccines", "vaccination", "shot", "shots", "rabies", "parvovirus", "parvo", "distemper",
            "vomit", "vomiting", "diarrhea", "stool", "poop", "pooping", "urine", "peeing", "urinary",
            "lethargic", "lethargy", "appetite", "limp", "limping", "scratch", "scratching", "itch", "itching",
            "cough", "coughing", "sneeze", "sneezing", "wheeze", "wheezing", "panting",
            "gum", "gums", "teeth", "tooth", "breath", "ear", "ears", "eye", "eyes",
            "groom", "grooming", "bath", "bathing", "shedding", "fur loss", "hairball",
            "neuter", "spay", "heat cycle", "pregnancy", "weaning", "bloat", "toxic", "poison", "poisoning",
            "eat", "eating", "food", "diet", "feed", "feeding", "treat", "treats"
        ]

        has_pet_kw = any(k in q_lower for k in pet_keywords)
        has_care_kw = any(k in q_lower for k in care_keywords)

        if has_pet_context:
            contextual_terms = ["he", "she", "him", "her", "eat", "food", "feed", "drink", "pain", "sleep", "safe", "hurt", "bad"]
            if any(term in q_lower for term in contextual_terms):
                return False

        return not (has_pet_kw or has_care_kw)

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

        # Check for out-of-topic query
        if cls.is_out_of_topic(clean_q, has_pet_context=(pet is not None)):
            return {
                "answer": (
                    f"I am VetVision AI, specialized exclusively in pet health, animal wellness, and veterinary care guidance. "
                    f"I cannot assist with questions outside of pet and animal topics.\n\n"
                    f"Please feel free to ask me anything about your pet's health, symptoms, diet, safe and toxic foods, "
                    f"vaccinations, grooming, training, or daily care!"
                ),
                "ai_engine": "VetVision Domain Scope Guardrail",
                "urgency_level": "GENERAL_INFO",
                "key_takeaways": [
                    "VetVision AI is dedicated exclusively to pet health and veterinary guidance.",
                    "Ask any questions regarding your pet's symptoms, nutrition, behavior, or wellness."
                ],
                "contraindications": [],
                "emergency_contacts": cls.EMERGENCY_CONTACTS,
                "pet_context": {
                    "name": pet_name,
                    "species": species.title(),
                    "assessment_id": assessment.id if assessment else None,
                    "assessment_risk": "UNKNOWN",
                },
                "disclaimer": (
                    "VetVision AI provides AI-assisted educational pet care guidance and supportive precautions. "
                    "It is not a substitute for clinical veterinary diagnosis, in-person examination, or prescription treatment."
                ),
            }

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
            # Check if groq responded with out-of-topic refusal
            if any(oot_phrase in groq_answer.lower() for oot_phrase in [
                "specialized exclusively", "only help with questions related to pets", "unrelated to those topics"
            ]):
                urgency = "GENERAL_INFO"
                key_takeaways = [
                    "VetVision AI is specialized in pet health, animal wellness, and veterinary care.",
                    "Ask questions about your dog, cat, bird, rabbit, or other pet's health, diet, or behavior."
                ]
                contraindications = []
            elif is_med_query or is_induce_vomit or is_emergency_signs:
                urgency = "EMERGENCY"
                key_takeaways = [
                    f"Guidance generated via {ai_engine} for {pet_name}.",
                    "Monitor vital indicators (gum color, breathing, hydration, posture).",
                    "Contact a licensed veterinarian or emergency clinic if condition worsens.",
                ]
                contraindications = [
                    "NEVER give human pain medications (acetaminophen, ibuprofen, aspirin).",
                    "NEVER induce vomiting at home without direct poison control instructions.",
                ]
            elif is_after_hours:
                urgency = "URGENT" if assessment_risk != "EMERGENCY" else "EMERGENCY"
                key_takeaways = [
                    f"Guidance generated via {ai_engine} for {pet_name}.",
                    "Locate nearest 24-hour emergency hospital and call ahead before departure.",
                ]
                contraindications = [
                    "Do not wait until morning if your pet has labored breathing, pale gums, or collapse.",
                ]
            elif is_vomit_single:
                urgency = "HOME_MONITORING" if assessment_risk in ["LOW", "UNKNOWN"] else "URGENT"
                key_takeaways = [
                    f"Guidance generated via {ai_engine} for {pet_name}.",
                    "Rest the stomach for 2-4 hours, then offer small sips of water.",
                    "Monitor for repeated vomiting, blood, or profound lethargy.",
                ]
                contraindications = [
                    "Do not give human antacids or stomach medications without veterinary dosage instructions.",
                ]
            else:
                urgency = assessment_risk if assessment_risk in ["EMERGENCY", "URGENT"] else "HOME_MONITORING"
                key_takeaways = [
                    f"Guidance generated via {ai_engine} for {pet_name}.",
                    "Observe your pet's appetite, energy level, and comfort closely.",
                    "Contact a licensed veterinarian if symptoms persist beyond 24 hours or worsen.",
                ]
                contraindications = [
                    "Never administer human medications or unverified supplements without veterinary approval.",
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

        # Domain 1: Toxic foods & substances
        elif any(k in q_lower for k in ["toxic", "poison", "chocolate", "xylitol", "grape", "raisin", "onion", "garlic", "lily", "lilies", "macadamia", "avocado"]):
            urgency = "EMERGENCY" if any(k in q_lower for k in ["ate", "swallowed", "ingested", "help"]) else "URGENT"
            answer = (
                f"CRITICAL TOXICITY INFORMATION FOR PETS ({pet_name.upper()}):\n\n"
                f"The following substances pose severe, life-threatening danger to pets:\n\n"
                f"• Xylitol / Birch Bark Sugar (Artificial Sweetener): Found in sugar-free gum, candy, peanut butter, and baked goods. "
                f"Causes massive insulin release, life-threatening hypoglycemia in 30 minutes, and acute liver failure.\n\n"
                f"• Chocolate & Caffeine: Contains theobromine. Dark chocolate and cocoa powder are most dangerous, causing arrhythmias, seizures, and death.\n\n"
                f"• Grapes & Raisins: Even a single grape or raisin can trigger irreversible acute kidney failure in dogs.\n\n"
                f"• Onions, Garlic, Leeks, & Chives: Destroys red blood cells, causing severe hemolytic anemia and lethargy.\n\n"
                f"• True Lilies (Tiger, Easter, Daylily): 100% fatal to cats! Even drinking water from the vase or licking pollen causes acute renal failure within 36 hours.\n\n"
                f"WHAT TO DO IF INGESTION OCCURRED:\n"
                f"Immediately contact ASPCA Animal Poison Control at (888) 426-4435 or your nearest emergency veterinary hospital. Do NOT induce vomiting at home."
            )
            key_takeaways = [
                "Xylitol, chocolate, grapes, onions, and lilies are acute pet poisons.",
                "True lilies cause fatal kidney failure in cats even in tiny amounts.",
                "Call ASPCA APCC at (888) 426-4435 immediately if ingestion occurred.",
            ]
            contraindications = [
                "Never give human foods containing sugar-free sweeteners without checking labels for xylitol.",
                "Never keep lilies in a household with cats.",
            ]

        # Domain 2: Safe human foods / treats
        elif any(k in q_lower for k in ["blueberry", "blueberries", "apple", "apples", "carrot", "carrots", "banana", "pumpkin", "safe food", "can eat", "safe fruit", "safe treat"]):
            urgency = "HOME_MONITORING"
            answer = (
                f"SAFE PET TREATS & NUTRITION GUIDANCE FOR {pet_name.upper()}:\n\n"
                f"Many fresh fruits and vegetables make excellent, nutritious treats for pets when prepared properly:\n\n"
                f"• Blueberries: Rich in antioxidants, fiber, and vitamins C and K. Feed fresh or frozen in moderation (3-6 berries for small pets, 8-12 for larger dogs).\n\n"
                f"• Apples: Excellent source of fiber and vitamins A & C. ALWAYS remove the core and seeds (apple seeds contain cyanogenic glycosides).\n\n"
                f"• Carrots: Low-calorie, high-fiber, and great for dental chewing. Serve raw in small bite-sized chunks or gently steamed.\n\n"
                f"• Plain Canned Pumpkin (Not pie mix): Gentle soluble fiber that regulates both mild diarrhea and constipation.\n\n"
                f"• Boiled Chicken & Rice: Ideal bland diet for temporary digestive recovery.\n\n"
                f"FEEDING RULES:\n"
                f"• Treats should never exceed 10% of {pet_name}'s daily caloric intake.\n"
                f"• Always wash produce and introduce any new food gradually to avoid gas or loose stool."
            )
            key_takeaways = [
                "Blueberries, deseeded apples, and carrots are safe, healthy treats.",
                "Always remove apple cores/seeds to avoid cyanide traces.",
                "Keep treats under 10% of total daily food intake.",
            ]
            contraindications = [
                "Never feed grapes, raisins, onions, garlic, or avocado.",
                "Never feed pumpkin pie filling containing spices or sweeteners.",
            ]

        # Domain 3: Ear issues, head shaking, scratching
        elif any(k in q_lower for k in ["ear", "scratching ear", "scratch ear", "head shake", "head shaking", "ear mite", "ear infection", "brown wax"]):
            urgency = "URGENT" if any(k in q_lower for k in ["odor", "discharge", "cry", "pain"]) else "HOME_MONITORING"
            answer = (
                f"EAR HEALTH & ITCHING ASSESSMENT FOR {pet_name.upper()}:\n\n"
                f"Frequent ear scratching and vigorous head shaking are key indicators of ear canal discomfort. Common causes include:\n\n"
                f"• Ear Infections (Bacterial or Yeast): Often accompanied by a pungent sour odor, red swollen ear flaps, and dark brown or yellowish discharge.\n\n"
                f"• Ear Mites (Otodectes cynotis): Microscopic parasites causing intense itching and dry, crumbly black debris resembling coffee grounds (very common in cats and outdoor pets).\n\n"
                f"• Environmental or Food Allergies: Causes inflammation and secondary yeast overgrowth in the ears and paws.\n\n"
                f"• Foreign Bodies: Grass seeds or foxtails lodged deep in the ear canal.\n\n"
                f"WHAT TO DO AT HOME:\n"
                f"1. Gently inspect the visible outer ear flap for redness, swelling, or odor.\n"
                f"2. Schedule a veterinary examination for an otoscopic inspection and ear cytology.\n"
                f"3. Never insert cotton swabs (Q-tips) into the ear canal, as this packs debris tightly against the eardrum and risks perforation."
            )
            key_takeaways = [
                "Persistent ear scratching indicates bacterial/yeast otitis, ear mites, or foreign bodies.",
                "Have a vet perform ear cytology to prescribe targeted antibacterial or antifungal drops.",
            ]
            contraindications = [
                "NEVER insert Q-tips or cotton swabs deep into the ear canal.",
                "Never apply alcohol, vinegar, or human ear drops into inflamed ears.",
            ]

        # Domain 4: Skin allergies, fleas, ticks, itching
        elif any(k in q_lower for k in ["flea", "fleas", "tick", "ticks", "itch", "itching", "scratch", "hot spot", "hair loss", "licking paw"]):
            urgency = "HOME_MONITORING"
            answer = (
                f"SKIN HEALTH, ITCHING, & PARASITE MANAGEMENT FOR {pet_name.upper()}:\n\n"
                f"Persistent skin itching, licking paws, and fur thinning commonly stem from these sources:\n\n"
                f"• Flea Allergy Dermatitis (FAD): A single flea bite can trigger severe allergic itching along the lower back, tail base, and thighs. Check for 'flea dirt' (black specks that turn reddish-brown when wet on a paper towel).\n\n"
                f"• Environmental Allergies (Atopy): Reaction to pollens, house dust mites, or molds, typically presenting as paw-licking, face-rubbing, and red bellies.\n\n"
                f"• Tick Bites: Inspect between toes, inside ears, under the collar, and groin. Use fine-tipped tweezers to pull ticks straight upward without twisting or squeezing the body.\n\n"
                f"RECOMMENDED CARE:\n"
                f"• Ensure {pet_name} is current on a monthly veterinarian-approved flea and tick preventative (e.g., isoxazoline chewables or topicals).\n"
                f"• Bathe with a soothing colloidal oatmeal pet shampoo using lukewarm water.\n"
                f"• If open sores, oozing 'hot spots', or scabs develop, seek veterinary treatment for prescription anti-itch therapy."
            )
            key_takeaways = [
                "Check for flea dirt along the base of the tail and underbelly.",
                "Maintain year-round veterinary-approved flea and tick preventatives.",
                "Remove ticks with fine-tipped tweezers pulling straight out.",
            ]
            contraindications = [
                "Never apply human anti-itch creams (hydrocortisone) that your pet can lick off.",
                "Never use dog flea products on cats (permethrin is fatal to felines).",
            ]

        # Domain 5: Diarrhea / loose stool
        elif any(k in q_lower for k in ["diarrhea", "loose stool", "runny stool", "runny poop", "soft poop", "watery stool"]):
            urgency = "URGENT" if any(k in q_lower for k in ["blood", "black", "lethargic", "vomit"]) else "HOME_MONITORING"
            answer = (
                f"DIARRHEA & DIGESTIVE MANAGEMENT FOR {pet_name.upper()}:\n\n"
                f"If {pet_name} has mild loose stool but remains energetic and alert, follow these home stabilization steps:\n\n"
                f"1. REST THE DIGESTIVE TRACT:\n"
                f"• Withhold rich treats, dairy, and fatty foods immediately.\n\n"
                f"2. TRANSITION TO A BLAND DIET (FOR 48 HOURS):\n"
                f"• Serve 2 parts boiled plain white rice mixed with 1 part boiled skinless white chicken breast (no oil, butter, salt, onion, or garlic).\n"
                f"• Add 1 tablespoon of plain canned pure pumpkin to provide soothing soluble fiber.\n\n"
                f"3. HYDRATION MAINTENANCE:\n"
                f"• Keep fresh room-temperature water accessible. Dehydration is the primary risk with persistent loose stool.\n\n"
                f"RED FLAGS REQUIRING IMMEDIATE VET ATTENTION:\n"
                f"• Stool contains bright red blood or appears black and tarry (melena).\n"
                f"• Diarrhea is accompanied by repeated vomiting, fever, or extreme lethargy.\n"
                f"• Symptoms persist for more than 48 hours without improvement."
            )
            key_takeaways = [
                "Feed a bland diet of boiled plain chicken, white rice, and plain pumpkin.",
                "Ensure steady water intake to prevent dangerous dehydration.",
                "Seek immediate veterinary care if blood is present or diarrhea exceeds 48 hours.",
            ]
            contraindications = [
                "Never give human anti-diarrheal medications (e.g., Pepto-Bismol contains salicylates toxic to cats and dogs).",
                "Do not feed dairy, bones, or oily table scraps.",
            ]

        # Domain 6: Respiratory, coughing, sneezing
        elif any(k in q_lower for k in ["cough", "coughing", "kennel cough", "sneeze", "sneezing", "wheezing", "breathing fast"]):
            urgency = "URGENT" if any(k in q_lower for k in ["struggling", "pale", "blue", "gasping"]) else "HOME_MONITORING"
            answer = (
                f"RESPIRATORY HEALTH EVALUATION FOR {pet_name.upper()}:\n\n"
                f"Respiratory symptoms in pets can range from mild self-limiting irritations to serious airway infections:\n\n"
                f"• Kennel Cough (Infectious Tracheobronchitis in Dogs): Presents as a harsh, dry, hacking cough resembling a honking goose, often triggered after boarding or dog park visits.\n\n"
                f"• Feline Asthma / Upper Respiratory Infection (in Cats): Presents with sneezing, eye discharge, or coughing while crouching low to the floor with an extended neck.\n\n"
                f"• Reverse Sneezing: Rapid, involuntary snorting inhalations through the nose; usually benign and stops when gently massaging the throat.\n\n"
                f"HOME OBSERVATION STEPS:\n"
                f"1. Measure resting respiratory rate while {pet_name} is sound asleep. A normal resting rate is under 30 breaths per minute.\n"
                f"2. Inspect gum color: Gums must remain salmon pink. Pale white, grey, or bluish gums are an immediate medical emergency.\n"
                f"3. Run a warm bathroom shower to create mild steam to soothe dry airways, and consult a vet if coughing lasts > 48 hours."
            )
            key_takeaways = [
                "Normal sleeping respiratory rate is under 30 breaths per minute.",
                "Gently soothe airways with bathroom shower steam for mild coughs.",
                "Open-mouth breathing in cats or bluish gums is an immediate emergency.",
            ]
            contraindications = [
                "Never administer human cough syrups or decongestants (pseudoephedrine and dextromethorphan are toxic).",
                "Avoid smoking, aerosols, scented candles, or essential oils around pets.",
            ]

        # Domain 7: Dental hygiene, bad breath
        elif any(k in q_lower for k in ["teeth", "tooth", "dental", "bad breath", "brush teeth", "tartar", "plaque", "gum"]):
            urgency = "HOME_MONITORING"
            answer = (
                f"DENTAL CARE & ORAL HEALTH FOR {pet_name.upper()}:\n\n"
                f"Over 80% of pets over 3 years old show signs of periodontal disease. Effective dental routines include:\n\n"
                f"• Tooth Brushing Routine: Use an enzymatic pet toothpaste (flavored like poultry or malt) and a soft finger toothbrush 2 to 3 times weekly.\n\n"
                f"• Halitosis (Bad Breath): Strong foul breath often indicates tartar buildup, subgingival bacterial infection, or tooth root abscess rather than simple dirty teeth.\n\n"
                f"• VOHC-Approved Chews: Look for dental chews and water additives certified by the Veterinary Oral Health Council (VOHC) to slow tartar accumulation.\n\n"
                f"• Professional Veterinary Dental Cleanings: Periodic subgingival ultrasonic scaling and polishing under veterinary anesthesia ensures deep tooth preservation."
            )
            key_takeaways = [
                "Brush teeth 2-3 times weekly with enzymatic pet toothpaste.",
                "Use VOHC-certified dental chews to reduce plaque.",
                "Have your vet perform regular dental examinations during annual wellness checks.",
            ]
            contraindications = [
                "NEVER use human toothpaste! Xylitol and fluoride are toxic and upset animal stomachs.",
                "Avoid ultra-hard bones or nylon chews that can fracture premolars and carnassial teeth.",
            ]

        # Domain 8: Vaccination & puppy/kitten schedule
        elif any(k in q_lower for k in ["vaccine", "vaccines", "vaccination", "shot", "shots", "puppy schedule", "kitten schedule", "deworm"]):
            urgency = "HOME_MONITORING"
            answer = (
                f"CORE VACCINATION & PREVENTIVE SCHEDULE FOR {pet_name.upper()}:\n\n"
                f"Vaccinations provide vital protection against fatal viral pathogens. Standard protocols include:\n\n"
                f"FOR PUPPIES & DOGS:\n"
                f"• 6 to 8 Weeks: DHPP (Distemper, Hepatitis, Parvovirus, Parainfluenza) + Deworming.\n"
                f"• 10 to 12 Weeks: DHPP Booster + Leptospirosis + Bordetella (Kennel Cough).\n"
                f"• 14 to 16 Weeks: Final DHPP Booster + Rabies (legally mandated) + Leptospirosis Booster.\n"
                f"• Adults: Annual or triennial boosters as guided by your veterinarian.\n\n"
                f"FOR KITTENS & CATS:\n"
                f"• 6 to 8 Weeks: FVRCP (Feline Viral Rhinotracheitis, Calicivirus, Panleukopenia) + Deworming.\n"
                f"• 10 to 12 Weeks: FVRCP Booster + FeLV (Feline Leukemia for outdoor cats).\n"
                f"• 14 to 16 Weeks: FVRCP Booster + Rabies Vaccine.\n\n"
                f"Keep young puppies/kittens away from public dog parks until 2 weeks after their final 16-week vaccination series."
            )
            key_takeaways = [
                "Puppies/kittens require boosters every 3-4 weeks from 6 to 16 weeks of age.",
                "Rabies vaccine is legally required and essential for all pets.",
                "Avoid public dog parks until 2 weeks after the full 16-week vaccine series.",
            ]
            contraindications = [
                "Do not skip puppy booster shots; maternal antibodies fade, leaving pups vulnerable to fatal parvo.",
            ]

        # Domain 9: Heatstroke & summer safety
        elif any(k in q_lower for k in ["heatstroke", "heat stroke", "hot car", "overheating", "panting heavy", "summer heat"]):
            urgency = "EMERGENCY"
            answer = (
                f"🚨 EMERGENCY HEATSTROKE & OVERHEATING PROTOCOL FOR {pet_name.upper()}:\n\n"
                f"Heatstroke occurs rapidly in hot weather, direct sun, or parked cars. Signs include heavy panting, drooling, brick-red gums, weakness, and vomiting.\n\n"
                f"IMMEDIATE FIRST AID COOLING STEPS:\n"
                f"1. Move {pet_name} into an air-conditioned room or cool shade immediately.\n"
                f"2. Apply COOL (NOT ICE-COLD) TAP WATER to the paws, groin, neck, and underbelly using wet towels.\n"
                f"3. Place a gentle fan blowing over the damp areas to encourage evaporative cooling.\n"
                f"4. Offer small sips of cool fresh water (never force-feed water).\n"
                f"5. Transport immediately to an emergency clinic with car air conditioning running.\n\n"
                f"CRITICAL WARNING:\n"
                f"Never immerse your pet in ice water or use ice packs directly on their body. Freezing temperatures constrict peripheral blood vessels, trapping dangerous heat inside vital core organs."
            )
            key_takeaways = [
                "Cool gradually with cool room-temperature water on paws, groin, and neck.",
                "Never leave pets unattended in parked vehicles even for a few minutes.",
                "Seek emergency veterinary transport immediately.",
            ]
            contraindications = [
                "NEVER use ice water baths or ice cubes; it causes vascular shock and traps core heat.",
                "Never force water down an unconscious or disoriented pet's throat.",
            ]

        # Domain 10: Specific Daily Companion Pets (Rabbits, Birds, Guinea Pigs, Hamsters, Reptiles)
        elif any(k in q_lower for k in ["rabbit", "bunny", "bird", "parrot", "guinea pig", "hamster", "turtle", "reptile"]):
            urgency = "HOME_MONITORING"
            answer = (
                f"SPECIALIZED COMPANION PET CARE GUIDANCE FOR {pet_name.upper()} ({species.upper()}):\n\n"
                f"• Rabbits: Diet must consist of 80% fresh Timothy hay, clean water, and fresh greens. CRITICAL: If a rabbit stops eating or producing fecal pellets for 10-12 hours, this is Gastrointestinal (GI) Stasis—a life-threatening emergency requiring immediate veterinary attention.\n\n"
                f"• Pet Birds: Birds have highly sensitive air sacs. Fumes from non-stick cookware (Teflon/PTFE), aerosol sprays, self-cleaning ovens, and scented candles are rapidly fatal to birds. Provide varied pellets, fresh vegetables, and seeds in moderation.\n\n"
                f"• Guinea Pigs: Guinea pigs cannot synthesize their own Vitamin C! They require daily dietary Vitamin C through fortified pellets, fresh bell peppers, and fresh Timothy hay.\n\n"
                f"• Hamsters: Provide deep dust-free paper bedding, solid-surface exercise wheels, and fresh water. Protect from drafts and extreme cold.\n\n"
                f"• Reptiles & Turtles: Require precise UVB lighting (replaced every 6-12 months) and species-specific thermal basking gradients with calcium supplementation."
            )
            key_takeaways = [
                "Rabbits require 80% Timothy hay; lack of eating for 12 hours is a GI stasis emergency.",
                "Birds must never be exposed to Teflon/PTFE fumes or aerosol sprays.",
                "Guinea pigs require daily dietary Vitamin C supplements and fresh hay.",
            ]
            contraindications = [
                "Never use non-stick Teflon cookware in homes with companion birds.",
                "Never withhold hay or water from rabbits or small herbivores.",
            ]

        else:
            # General Evidence-Grounded Contextual Response
            urgency = assessment_risk if assessment_risk in ["EMERGENCY", "URGENT"] else "HOME_MONITORING"
            symptom_str = f"Based on {pet_name}'s recent reported symptoms ({', '.join(assessment_symptoms) if assessment_symptoms else 'general observation'}): " if assessment_symptoms else ""

            answer = (
                f"{symptom_str}Here is safe, owner-focused supportive guidance for {pet_name} ({species.title()}):\n\n"
                f"• COMFORT & REST: Keep {pet_name} in a comfortable, quiet, well-ventilated space with easy access to fresh water and clean bedding. Minimize loud noises and physical exertion.\n\n"
                f"• SUPPORTIVE MONITORING: Check gum color, breathing rhythm, hydration (skin elasticity), and activity level every 2 to 3 hours.\n\n"
                f"• HYDRATION & NOURISHMENT: Always provide clean fresh water. Never force-feed or syringe liquids into {pet_name}'s mouth if they are reluctant or nauseous.\n\n"
                f"• WHEN TO CONTACT YOUR VET: If symptoms persist beyond 24 hours, worsen in intensity, or if {pet_name} develops repeated vomiting, breathing changes, or weakness, schedule a prompt veterinary examination."
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

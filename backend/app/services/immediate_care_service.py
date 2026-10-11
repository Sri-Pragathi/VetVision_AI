"""ImmediateCareService — Evidence-based, safety-first veterinary care guidance library and synthesis engine.

Provides structured, symptom-specific first-aid, comfort measures, contraindications,
and triage escalation thresholds for pet owners while strictly enforcing safety guardrails.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


# ---------------------------------------------------------------------------
# EVIDENCE-BASED GUIDANCE KNOWLEDGE BASE (12 SUPPORTED SCENARIOS)
# ---------------------------------------------------------------------------
IMMEDIATE_CARE_LIBRARY: Dict[str, Dict[str, Any]] = {
    "vomiting_diarrhea": {
        "condition_key": "vomiting_diarrhea",
        "title": "Vomiting and Diarrhoea",
        "applicable_species": ["dog", "cat", "any"],
        "evidence_sources": [
            {
                "organization": "American Animal Hospital Association (AAHA)",
                "title": "Canine and Feline Fluid and Gastrointestinal Care Guidelines",
                "review_date": "2025-08-15",
                "clinician_reviewed": True,
            },
            {
                "organization": "Cornell Feline Health Center",
                "title": "Feline Gastrointestinal Health and Dehydration Risks",
                "review_date": "2025-06-20",
                "clinician_reviewed": True,
            },
        ],
        "reviewer_status": "reviewed_by_veterinary_board",
        "default_urgency": "URGENT",
        "what_to_do_now": [
            "Provide calm, quiet rest in an easy-to-clean, comfortable area away from stressors.",
            "Offer small, controlled sips of fresh, room-temperature water every 30-60 minutes rather than large bowls if the pet has kept liquids down for at least 2 hours.",
            "Do not withhold water completely unless the pet is actively vomiting immediately after drinking.",
            "Keep the pet warm and monitor the color of their gums (should be moist and bubblegum pink).",
            "Separate the ill pet from other household animals to monitor output and prevent contagion.",
        ],
        "what_to_avoid": [
            "DO NOT administer human anti-diarrheal or anti-nausea medications (e.g., Pepto-Bismol, Imodium, Kaopectate); Pepto-Bismol contains bismuth subsalicylate which is toxic to cats and dangerous for dogs.",
            "DO NOT force-feed food, liquids, or milk via syringe; this can cause deadly aspiration into the lungs.",
            "DO NOT offer fatty treats, table scraps, dairy products, or rich broth.",
            "DO NOT induce vomiting at home with hydrogen peroxide, salt, or oils.",
        ],
        "what_to_monitor": [
            "Frequency and volume of vomitus and stool.",
            "Presence of blood (bright red streaks or dark coffee-ground appearance).",
            "Signs of dehydration: dry or sticky gums, sunken eyes, loss of skin elasticity (skin tenting).",
            "Lethargy, weakness, unresponsiveness, or inability to stand.",
            "Abdominal distension, restlessness, or praying posture (arched back, forelimbs down).",
        ],
        "when_to_see_vet": {
            "emergency_threshold": "Vomiting more than 3 times in 24 hours, blood in vomitus or stool, extreme lethargy, or signs of abdominal pain require immediate emergency veterinary evaluation.",
            "urgent_threshold": "Persistent diarrhea or vomiting lasting more than 12-24 hours without improvement requires prompt veterinary examination.",
            "home_monitoring_conditions": "A single mild episode in an otherwise bright, alert, adult pet with no blood, normal gums, and no pre-existing conditions may be monitored for 12 hours.",
        },
        "species_notes": {
            "cat": "Feline hepatic lipidosis (fatty liver) can develop rapidly if a cat goes without food for >24-48 hours. Cats with repeated vomiting must be evaluated sooner than dogs.",
            "dog": "Large deep-chested dogs exhibiting unproductive retching and a bloated abdomen must be evaluated for Gastric Dilatation-Volvulus (GDV/Bloat) immediately.",
        },
    },

    "reduced_appetite": {
        "condition_key": "reduced_appetite",
        "title": "Reduced Appetite (Anorexia / Hyporexia)",
        "applicable_species": ["dog", "cat", "any"],
        "evidence_sources": [
            {
                "organization": "American Veterinary Medical Association (AVMA)",
                "title": "Nutritional Support and Early Disease Detection in Companion Animals",
                "review_date": "2025-07-10",
                "clinician_reviewed": True,
            },
            {
                "organization": "Cornell Feline Health Center",
                "title": "Anorexia in Cats and Risk of Hepatic Lipidosis",
                "review_date": "2025-09-01",
                "clinician_reviewed": True,
            },
        ],
        "reviewer_status": "reviewed_by_veterinary_board",
        "default_urgency": "APPOINTMENT_RECOMMENDED",
        "what_to_do_now": [
            "Ensure the pet has free access to fresh, clean water in a shallow, accessible dish.",
            "Offer small portions of mild, gently warmed food (plain boiled chicken and white rice for dogs, plain warmed wet food for cats) to enhance aroma.",
            "Place food dishes in a quiet, low-traffic environment away from loud appliances or other pets.",
            "Inspect the mouth visually from a distance for visible dental debris, drooling, or facial swelling without prying jaws open forcefully.",
        ],
        "what_to_avoid": [
            "DO NOT force-feed by pushing food or syringes into the mouth, which causes food aversion and severe aspiration pneumonia risk.",
            "DO NOT use human appetite stimulants, anti-depressants, or unprescribed animal medications.",
            "DO NOT feed seasoned food, onions, garlic, chives, raisins, grapes, or xylitol-containing foods.",
        ],
        "what_to_monitor": [
            "Total duration since the last complete meal.",
            "Concurrent vomiting, diarrhea, jaundice (yellowing of skin/eyes/gums), or marked lethargy.",
            "Water intake (either complete refusal or abnormally excessive drinking).",
            "Unexplained weight loss or muscle wasting.",
        ],
        "when_to_see_vet": {
            "emergency_threshold": "Complete refusal of food and water for >24 hours accompanied by lethargy, jaundice, or fever requires emergency veterinary care.",
            "urgent_threshold": "Any cat that has not eaten for 24-48 hours must see a vet promptly to prevent feline hepatic lipidosis.",
            "home_monitoring_conditions": "A healthy adult dog that skips one meal but remains active, playful, and drinks water normally may be gently monitored for 12-24 hours.",
        },
        "species_notes": {
            "cat": "CRITICAL: Cats that do not eat for 48 hours are at high risk of fatal liver failure (hepatic lipidosis). Do not delay veterinary assessment for an anorexic cat.",
            "dog": "Puppies under 6 months cannot tolerate prolonged fasting due to hypoglycemia risk.",
        },
    },

    "behavior_energy_changes": {
        "condition_key": "behavior_energy_changes",
        "title": "Changes in Behaviour or Energy",
        "applicable_species": ["dog", "cat", "any"],
        "evidence_sources": [
            {
                "organization": "American Animal Hospital Association (AAHA)",
                "title": "Behavioral Management and Clinical Pain Recognition Guidelines",
                "review_date": "2025-05-12",
                "clinician_reviewed": True,
            },
        ],
        "reviewer_status": "reviewed_by_veterinary_board",
        "default_urgency": "APPOINTMENT_RECOMMENDED",
        "what_to_do_now": [
            "Provide a quiet, dim, stress-free resting zone with familiar bedding.",
            "Minimize loud noises, sudden movements, and visitors.",
            "Observe the pet's posture: look for stiffness, shivering, reluctance to lie down, or curled-up hiding.",
            "Check that comfortable access to water and the litter box / elimination area is unimpeded.",
        ],
        "what_to_avoid": [
            "DO NOT administer human sedatives, tranquilizers, or sleep aids.",
            "DO NOT punish, scold, or force the pet out of hiding; defensive aggression or fear bites can occur when pets are in pain.",
            "DO NOT ignore subtle behavioral changes in cats, who instinctively mask symptoms of severe pain or illness.",
        ],
        "what_to_monitor": [
            "Unresponsiveness, dullness, or inability to wake from sleep.",
            "Sudden aggressive reactions when touched in specific areas (indicating acute pain).",
            "Disorientation, head pressing against walls, pacing, or loss of balance.",
        ],
        "when_to_see_vet": {
            "emergency_threshold": "Collapse, unresponsiveness, head pressing, or sudden inability to stand requires immediate emergency transportation.",
            "urgent_threshold": "Pronounced lethargy persisting beyond 24 hours warrants a prompt veterinary exam.",
            "home_monitoring_conditions": "Mild sleepiness following an unusually active day in an otherwise healthy pet can be observed for 12 hours.",
        },
        "species_notes": {
            "cat": "Cats express pain through hiding, squinting, hunched posture (feline grimace scale), and neglect of grooming.",
            "dog": "Dogs often pant, pace, tremble, or become unusually clingy when in discomfort.",
        },
    },

    "skin_irritation_itching": {
        "condition_key": "skin_irritation_itching",
        "title": "Skin Irritation and Itching",
        "applicable_species": ["dog", "cat", "any"],
        "evidence_sources": [
            {
                "organization": "World Small Animal Veterinary Association (WSAVA)",
                "title": "Companion Animal Dermatology and Pruritus Clinical Protocol",
                "review_date": "2025-04-18",
                "clinician_reviewed": True,
            },
        ],
        "reviewer_status": "reviewed_by_veterinary_board",
        "default_urgency": "APPOINTMENT_RECOMMENDED",
        "what_to_do_now": [
            "Apply a cool, damp cloth or cool water compress to the irritated skin for 5-10 minutes to soothe inflammation.",
            "Use an Elizabethan collar (cone) or recovery suit to prevent self-trauma, lick granulomas, or secondary bacterial infection.",
            "Keep the pet in a cool, low-humidity indoor environment.",
            "Take clear, well-lit photos of the skin lesions to show your veterinarian.",
        ],
        "what_to_avoid": [
            "DO NOT apply human hydrocortisone creams, antibiotic ointments, tea tree oil, or calamine lotion; many are toxic if licked.",
            "DO NOT use human shampoos or dish soaps, which disrupt the natural pet skin lipid barrier.",
            "DO NOT give over-the-counter human antihistamines without a veterinarian's direct dosage instruction.",
        ],
        "what_to_monitor": [
            "Rapid spread of redness, hives, swelling of the face, muzzle, or eyes (possible acute anaphylaxis).",
            "Discharge of foul-smelling pus, weeping open hot spots, or bleeding.",
            "Signs of intense distress, whining, or inability to rest due to unrelenting pruritus.",
        ],
        "when_to_see_vet": {
            "emergency_threshold": "Facial swelling, hives with labored breathing, or acute allergic reaction requires emergency care.",
            "urgent_threshold": "Open weeping hot spots or extensive raw skin areas should be seen by a veterinarian within 24 hours.",
            "home_monitoring_conditions": "Mild, intermittent itching with intact skin and no lesions can be discussed at a routine veterinary appointment.",
        },
        "species_notes": {
            "cat": "Cats can develop severe eosinophilic granulomas and miliary dermatitis rapidly from allergic triggers.",
            "dog": "Dogs are especially prone to acute moist dermatitis (hot spots) during warm, humid weather.",
        },
    },

    "minor_wounds": {
        "condition_key": "minor_wounds",
        "title": "Minor Superficial Wounds and Scratches",
        "applicable_species": ["dog", "cat", "any"],
        "evidence_sources": [
            {
                "organization": "British Small Animal Veterinary Association (BSAVA)",
                "title": "Manual of Canine and Feline Wound Management and First Aid",
                "review_date": "2025-03-10",
                "clinician_reviewed": True,
            },
        ],
        "reviewer_status": "reviewed_by_veterinary_board",
        "default_urgency": "APPOINTMENT_RECOMMENDED",
        "what_to_do_now": [
            "Gently flush the superficial scratch with sterile saline or clean, lukewarm tap water to rinse away debris.",
            "Gently pat the area dry using clean, sterile gauze.",
            "Apply gentle, direct pressure with clean gauze for 3-5 minutes if there is very minor capillary bleeding.",
            "Fit an Elizabethan collar (cone) to prevent the pet from licking or chewing the wound.",
        ],
        "what_to_avoid": [
            "DO NOT apply hydrogen peroxide, rubbing alcohol, or iodine; they damage living granulation tissue and delay wound healing.",
            "DO NOT apply human triple-antibiotic ointments containing zinc or bacitracin if the pet can lick it off.",
            "DO NOT apply tight bandages, tourniquets, or adhesive tape directly to fur; improper bandaging cuts off blood supply.",
        ],
        "what_to_monitor": [
            "Active spurting or continuous bleeding that does not stop after 5 minutes of firm pressure.",
            "Deep punctures, gaping tissue edges, exposure of fat, muscle, or bone.",
            "Heat, foul odor, swelling, or yellow/green purulent discharge indicating infection.",
        ],
        "when_to_see_vet": {
            "emergency_threshold": "Arterial or uncontrolled bleeding, bite wounds penetrating deep muscle, or puncture wounds near joints/chest require immediate emergency transport.",
            "urgent_threshold": "Bite wounds from another animal always require prompt veterinary evaluation and systemic antibiotics within 12-24 hours.",
            "home_monitoring_conditions": "Tiny, superficial abrasions with no bleeding and no depth may be kept clean and monitored at home.",
        },
        "species_notes": {
            "cat": "Cat bite wounds harbor Pasteurella multocida and rapidly form painful, deep abscesses if not treated with antibiotics promptly.",
            "dog": "Dog bite wounds often have substantial underlying tissue damage ('iceberg effect') despite small puncture holes in the skin.",
        },
    },

    "limping_injury": {
        "condition_key": "limping_injury",
        "title": "Limping or Suspected Musculoskeletal Injury",
        "applicable_species": ["dog", "cat", "any"],
        "evidence_sources": [
            {
                "organization": "American College of Veterinary Surgeons (ACVS)",
                "title": "Clinical Guidelines on Lameness and Orthopedic First Aid",
                "review_date": "2025-06-05",
                "clinician_reviewed": True,
            },
        ],
        "reviewer_status": "reviewed_by_veterinary_board",
        "default_urgency": "APPOINTMENT_RECOMMENDED",
        "what_to_do_now": [
            "Enforce strict crate or small-room rest; restrict running, jumping on furniture, stairs, and rough play.",
            "Inspect paw pads carefully for thorns, glass, burrs, cracked nails, or foreign objects between toes.",
            "Take the pet outdoors for elimination strictly on a short hand-held leash.",
            "Provide padded, non-slip bedding on ground level.",
        ],
        "what_to_avoid": [
            "DO NOT give human pain medications: Ibuprofen (Advil), Naproxen (Aleve), Acetaminophen (Tylenol), or Aspirin cause fatal kidney failure, gastric ulcers, and methemoglobinemia in pets.",
            "DO NOT manipulate, twist, or aggressively bend the injured limb to 'test' the joint.",
            "DO NOT apply human heating pads or ice packs directly to skin without veterinary instruction.",
        ],
        "what_to_monitor": [
            "Complete refusal to bear weight (carrying the leg entirely off the ground).",
            "Visible angulation, deformity, swelling, or open bone exposure (fracture).",
            "Limb coolness to touch or loss of motor function/dragging paws (possible vascular or spinal paralysis).",
            "Vocalization, crying out, or aggression when approaching the affected limb.",
        ],
        "when_to_see_vet": {
            "emergency_threshold": "Non-weight-bearing lameness after high-impact trauma, visible deformity, dragging legs, or severe distress requires immediate emergency care.",
            "urgent_threshold": "Lameness that does not improve after 24 hours of strict rest requires veterinary orthopedic evaluation.",
            "home_monitoring_conditions": "A very mild, temporary hitch in gait that resolves completely within 1-2 hours of quiet rest with normal weight-bearing may be monitored.",
        },
        "species_notes": {
            "cat": "Sudden hind-limb paralysis in cats accompanied by cold paws and crying is often Feline Aortic Thromboembolism ('saddle thrombus') — a life-threatening medical emergency.",
            "dog": "Active large-breed dogs commonly suffer cranial cruciate ligament (CCL) tears requiring orthopedic diagnosis.",
        },
    },

    "heat_exposure": {
        "condition_key": "heat_exposure",
        "title": "Heat Exposure and Early Heat Stress",
        "applicable_species": ["dog", "cat", "any"],
        "evidence_sources": [
            {
                "organization": "Veterinary Emergency and Critical Care Society (VECCS)",
                "title": "Heatstroke in Small Animals: Recognition and First Aid Protocol",
                "review_date": "2025-07-22",
                "clinician_reviewed": True,
            },
        ],
        "reviewer_status": "reviewed_by_veterinary_board",
        "default_urgency": "EMERGENCY",
        "what_to_do_now": [
            "Immediately move the pet into a cool, air-conditioned indoor area or shaded, ventilated space.",
            "Apply cool (NOT ice-cold) water to the pet's paws, abdomen, groin, and neck using damp towels or gentle tap water.",
            "Place a fan blowing cool air directly across the damp pet to promote evaporative cooling.",
            "Offer small sips of cool drinking water, but never force water down the throat.",
            "Stop active cooling once the pet's temperature reaches 103°F (39.4°C) to prevent hypothermic rebound shock.",
        ],
        "what_to_avoid": [
            "DO NOT use ice, ice water baths, or freezing water; this causes peripheral vasoconstriction, trapping lethal heat inside the core organs.",
            "DO NOT leave wet towels draped over the pet; they rapidly trap heat like a sauna blanket once warmed.",
            "DO NOT delay transport to an emergency clinic; heatstroke causes rapid multi-organ failure and disseminated intravascular coagulation (DIC).",
        ],
        "what_to_monitor": [
            "Excessive, frantic panting that does not subside after 10 minutes of cooling.",
            "Bright brick-red or bluish-purple gums, or dark petechial bruising.",
            "Thick, ropey saliva, vomiting, bloody diarrhea, or unsteadiness/collapse.",
            "Seizures, stupor, or loss of consciousness.",
        ],
        "when_to_see_vet": {
            "emergency_threshold": "Any pet that has suffered acute heat exposure with elevated body temperature, stumbling, or heavy panting must be evaluated by an emergency veterinarian immediately, even if they appear to recover.",
            "urgent_threshold": "Not applicable — heatstroke is always an immediate medical emergency.",
            "home_monitoring_conditions": "Never monitor suspected heatstroke at home.",
        },
        "species_notes": {
            "cat": "Panting in cats is almost never normal; open-mouth breathing combined with heat exposure indicates critical distress.",
            "dog": "Brachycephalic breeds (Pugs, Bulldogs, Boxers) are exceptionally vulnerable to fatal heatstroke even at moderate temperatures.",
        },
    },

    "eye_irritation": {
        "condition_key": "eye_irritation",
        "title": "Eye Irritation and Discharge",
        "applicable_species": ["dog", "cat", "any"],
        "evidence_sources": [
            {
                "organization": "American College of Veterinary Ophthalmologists (ACVO)",
                "title": "Ophthalmic Emergency Evaluation and Cornea Care",
                "review_date": "2025-04-02",
                "clinician_reviewed": True,
            },
        ],
        "reviewer_status": "reviewed_by_veterinary_board",
        "default_urgency": "URGENT",
        "what_to_do_now": [
            "Gently flush the eye with sterile saline eye wash (WITHOUT medications or preservatives) to clear dust or minor foreign material.",
            "Place an Elizabethan collar (cone) on immediately to prevent rubbing, pawing, or corneal ulcer perforation.",
            "Keep the pet in a softly lit or dim room to reduce photophobic discomfort.",
            "Gently wipe away outer eyelid discharge with a clean, moist gauze pad.",
        ],
        "what_to_avoid": [
            "DO NOT use human eye drops (e.g., Visine, redness relievers) which cause severe vascular constriction.",
            "DO NOT use leftover ophthalmic ointments containing steroids (dexamethasone, hydrocortisone); if a corneal ulcer is present, steroids can cause the eye to rupture within 24-48 hours.",
            "DO NOT attempt to remove an embedded foreign object from the eyeball.",
        ],
        "what_to_monitor": [
            "Persistent squinting, blepharospasm, or inability to open the eye.",
            "Cloudiness, bluish haze, or visible dent/ulcer on the clear corneal surface.",
            "Thick green or yellow purulent discharge, or bleeding.",
            "Pupil size asymmetry (anisocoria) or protrusion of the eyeball.",
        ],
        "when_to_see_vet": {
            "emergency_threshold": "Eyeball prolapse, visible corneal laceration, acute blindness, or severe trauma requires immediate emergency ophthalmology care.",
            "urgent_threshold": "Any painful, squinting, or cloudy eye must be evaluated within 12-24 hours to prevent permanent loss of vision.",
            "home_monitoring_conditions": "Very mild clear watering after wind exposure that resolves fully within an hour with no squinting can be gently observed.",
        },
        "species_notes": {
            "cat": "Feline Herpesvirus-1 (FHV-1) is a common cause of chronic painful keratitis and corneal sequestrum in cats.",
            "dog": "Exophthalmic breeds (Shih Tzus, Pugs) are prone to rapid corneal drying and traumatic proptosis.",
        },
    },

    "poisoning": {
        "condition_key": "poisoning",
        "title": "Possible Poisoning or Toxic Exposure",
        "applicable_species": ["dog", "cat", "any"],
        "evidence_sources": [
            {
                "organization": "ASPCA Animal Poison Control Center (APCC)",
                "title": "Emergency Toxicology Protocol and Decontamination Guidelines",
                "review_date": "2025-08-01",
                "clinician_reviewed": True,
            },
            {
                "organization": "Pet Poison Helpline",
                "title": "Critical Toxins and Emergency Response Standards",
                "review_date": "2025-07-15",
                "clinician_reviewed": True,
            },
        ],
        "reviewer_status": "reviewed_by_veterinary_board",
        "default_urgency": "EMERGENCY",
        "what_to_do_now": [
            "IMMEDIATELY contact an open emergency veterinary hospital, ASPCA Animal Poison Control (888-426-4435), or Pet Poison Helpline (855-764-7661).",
            "Immediately remove the pet from the toxic source to prevent further ingestion or exposure.",
            "Safely collect the exact packaging, container, label, plant sample, or remaining substance to show the veterinarian.",
            "Note the exact estimated time of exposure, amount ingested, and active ingredients.",
            "If toxin is on the coat or skin, gently wash with lukewarm water and mild dish soap to prevent grooming ingestion.",
        ],
        "what_to_avoid": [
            "DO NOT induce vomiting unless explicitly commanded by a licensed veterinary toxicologist; inducing vomiting for caustic chemicals, batteries, petroleum products, or in a lethargic pet can cause fatal esophageal burning and aspiration.",
            "DO NOT administer salt, mustard, milk, raw eggs, vegetable oil, or activated charcoal without veterinary instruction.",
            "DO NOT wait for clinical symptoms to appear; many fatal toxins (e.g., lilies in cats, antifreeze, rat poison) cause irreversible kidney or organ damage before outward symptoms show.",
        ],
        "what_to_monitor": [
            "Tremors, muscle twitching, seizures, or incoordination (ataxia).",
            "Vomiting, diarrhea, drooling, or abnormal pupil dilation/constriction.",
            "Sudden lethargy, collapse, or difficulty breathing.",
        ],
        "when_to_see_vet": {
            "emergency_threshold": "ALL confirmed or suspected poisonings require immediate emergency veterinary consultation and rapid decontamination.",
            "urgent_threshold": "Not applicable — toxic ingestion is always an immediate emergency.",
            "home_monitoring_conditions": "Never monitor suspected poisoning at home.",
        },
        "species_notes": {
            "cat": "CRITICAL: All true lilies (Lilium and Hemerocallis spp.) are lethally toxic to cats; even grooming pollen or drinking vase water causes fatal acute kidney failure. Pyrethrin/permethrin flea treatments for dogs are lethal neurotoxins to cats.",
            "dog": "Common canine toxins include chocolate (theobromine), xylitol/birch sugar (causes acute liver failure and hypoglycemia), grapes/raisins, NSAIDs, and rodenticides.",
        },
    },

    "difficulty_breathing": {
        "condition_key": "difficulty_breathing",
        "title": "Difficulty Breathing (Respiratory Distress / Dyspnea)",
        "applicable_species": ["dog", "cat", "any"],
        "evidence_sources": [
            {
                "organization": "Veterinary Emergency and Critical Care Society (VECCS)",
                "title": "Triage and Stabilization of Small Animal Respiratory Emergencies",
                "review_date": "2025-06-18",
                "clinician_reviewed": True,
            },
        ],
        "reviewer_status": "reviewed_by_veterinary_board",
        "default_urgency": "EMERGENCY",
        "what_to_do_now": [
            "TRANSPORT TO THE NEAREST EMERGENCY VETERINARY CLINIC IMMEDIATELY.",
            "Keep the pet as calm and quiet as possible; acute anxiety dramatically accelerates respiratory collapse.",
            "Transport in a secure, well-ventilated carrier or crate with the vehicle air-conditioning running.",
            "Call the receiving emergency veterinary hospital ahead of time so they can prepare supplemental oxygen cages and immediate triage.",
            "Minimize handling; do not restrain or compress the chest, neck, or abdomen.",
        ],
        "what_to_avoid": [
            "DO NOT force the pet into a lying position or hold their mouth closed.",
            "DO NOT attempt mouth-to-snout resuscitation unless the pet has completely collapsed and stopped breathing.",
            "DO NOT give any water, food, or oral medications; choking and fatal aspiration will occur.",
            "DO NOT wait to see if breathing improves overnight.",
        ],
        "what_to_monitor": [
            "Open-mouth breathing, extended neck, flared nostrils, or abducted elbows.",
            "Blue, grey, purple, or pale gums/tongue (cyanosis indicating severe hypoxia).",
            "Abdominal effort: deep heave of the belly to breathe.",
            "Noisy, stridulous, or raspy breathing sounds.",
        ],
        "when_to_see_vet": {
            "emergency_threshold": "Difficulty breathing is a life-threatening medical emergency. Seek immediate veterinary emergency hospital care without delay.",
            "urgent_threshold": "Not applicable — respiratory distress is always an immediate emergency.",
            "home_monitoring_conditions": "Never monitor respiratory distress at home.",
        },
        "species_notes": {
            "cat": "Open-mouth breathing in a cat is a hallmark of severe, critical respiratory decompensation (asthma, pleural effusion, or congestive heart failure). Immediate oxygen therapy is required.",
            "dog": "Tracheal collapse, laryngeal paralysis, and congestive heart failure require urgent clinical stabilization.",
        },
    },

    "seizures_collapse": {
        "condition_key": "seizures_collapse",
        "title": "Seizures or Sudden Collapse",
        "applicable_species": ["dog", "cat", "any"],
        "evidence_sources": [
            {
                "organization": "American College of Veterinary Internal Medicine (ACVIM)",
                "title": "Consensus Statement on the Management of Status Epilepticus in Dogs and Cats",
                "review_date": "2025-05-30",
                "clinician_reviewed": True,
            },
        ],
        "reviewer_status": "reviewed_by_veterinary_board",
        "default_urgency": "EMERGENCY",
        "what_to_do_now": [
            "Keep the pet safe: gently move sharp objects, hard edges, stairs, or furniture away so they do not injure themselves.",
            "Turn off bright lights and quiet the room to reduce neurological stimulation.",
            "Time the seizure with a stopwatch or clock.",
            "Place soft pillows or blankets around (not over) the pet.",
            "Once convulsions cease, stay with the pet quietly while they navigate the disoriented post-ictal phase.",
        ],
        "what_to_avoid": [
            "DO NOT put your hands, fingers, or objects in the pet's mouth; pets DO NOT swallow their tongues during seizures, and severe involuntary bite injuries will occur.",
            "DO NOT restrain the pet's limbs during active convulsions.",
            "DO NOT offer food, water, or medication until the pet is fully conscious and alert.",
        ],
        "what_to_monitor": [
            "Seizure duration: any seizure lasting longer than 3-5 minutes is status epilepticus and causes irreversible brain damage without emergency medication.",
            "Cluster seizures: more than one seizure within a 24-hour period.",
            "Difficulty breathing, hyperthermia (high body heat), or prolonged unresponsiveness following the episode.",
        ],
        "when_to_see_vet": {
            "emergency_threshold": "A seizure lasting >3 minutes, cluster seizures (2+ in 24 hours), or sudden collapse with pale gums requires immediate emergency transport.",
            "urgent_threshold": "A first-time brief (<1 minute) isolated seizure in a pet that returns to normal within 15 minutes requires urgent evaluation within 12 hours.",
            "home_monitoring_conditions": "Never monitor status epilepticus or unresponsiveness at home.",
        },
        "species_notes": {
            "cat": "Seizures in cats frequently point to severe underlying systemic toxicity, infectious encephalitis, or intracranial disease.",
            "dog": "Idiopathic epilepsy is common in young dogs, but acute toxicity (snail bait, organophosphates) must always be ruled out.",
        },
    },

    "difficulty_urinating": {
        "condition_key": "difficulty_urinating",
        "title": "Difficulty Urinating (Straining / Dysuria / Feline Urethral Blockage)",
        "applicable_species": ["dog", "cat", "any"],
        "evidence_sources": [
            {
                "organization": "American Association of Feline Practitioners (AAFP)",
                "title": "Guidelines on Feline Lower Urinary Tract Disease and Obstructive Uropathy",
                "review_date": "2025-08-10",
                "clinician_reviewed": True,
            },
            {
                "organization": "American Animal Hospital Association (AAHA)",
                "title": "Canine Urolithiasis and Lower Urinary Tract Disorders",
                "review_date": "2025-06-14",
                "clinician_reviewed": True,
            },
        ],
        "reviewer_status": "reviewed_by_veterinary_board",
        "default_urgency": "EMERGENCY",
        "what_to_do_now": [
            "FOR CATS: Check the litter box immediately to verify whether any urine is actually being produced.",
            "If a cat (especially male) strains and produces only drops or no urine, TRANSPORT TO EMERGENCY IMMEDIATELY.",
            "Keep the pet calm, contained, and prevent active running or stress.",
            "Collect a clean, fresh urine sample in a sterile cup ONLY if the pet voids naturally while awaiting transport.",
        ],
        "what_to_avoid": [
            "DO NOT assume a straining cat is 'constipated'; in 90% of cases, owners confuse urinary blockage with constipation, leading to fatal delays.",
            "DO NOT squeeze, press, or palpate the pet's bladder/abdomen; an obstructed bladder can rupture, causing fatal peritonitis.",
            "DO NOT give human cranberry extract, urinary medications, or antibiotics without veterinary prescription.",
        ],
        "what_to_monitor": [
            "Frequent trips to the box with crying, vocalizing, or licking genitals intensely.",
            "Vomiting, profound lethargy, cold paws, or collapse (indicating acute uremic poisoning and hyperkalemia).",
            "Blood in urine (hematuria).",
        ],
        "when_to_see_vet": {
            "emergency_threshold": "Inability to pass urine in cats is a 100% fatal medical emergency within 24-48 hours due to potassium cardiac arrest. Immediate emergency unblocking is required.",
            "urgent_threshold": "Frequent urination with small volume production in an otherwise bright dog requires veterinary testing for infection/stones within 24 hours.",
            "home_monitoring_conditions": "Never monitor urinary straining without confirmed normal volume production.",
        },
        "species_notes": {
            "cat": "CRITICAL EMERGENCY: Male cats have a very narrow urethra easily plugged by crystals or spasms. A blocked cat will suffer heart failure and die within 24 to 48 hours without clinical catheterization.",
            "dog": "Canine urinary blockages occur due to bladder stones and require urgent surgical or medical relief.",
        },
    },
}


# ---------------------------------------------------------------------------
# IMMEDIATE CARE SYNTHESIS ENGINE
# ---------------------------------------------------------------------------
class ImmediateCareService:
    """Core synthesis engine for evidence-based immediate care and safety guidance."""

    STANDARD_DISCLAIMER = (
        "VetVision AI provides AI-assisted supportive guidance, early-warning health indicators, "
        "and triage safety instructions for informational purposes. It does not provide a confirmed "
        "veterinary diagnosis and does not establish a veterinarian-client-patient relationship. "
        "Home supportive care does not treat or cure underlying illnesses. In cases of acute injury, "
        "toxic exposure, respiratory distress, or severe symptoms, consult an emergency veterinarian immediately."
    )

    @classmethod
    def get_library(cls) -> Dict[str, Dict[str, Any]]:
        """Retrieve the official evidence-based veterinary guidance knowledge base."""
        return IMMEDIATE_CARE_LIBRARY

    @classmethod
    def get_guidance_for_condition(
        cls, condition_key: str, species: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a specific guidance entry with species adaptations."""
        entry = IMMEDIATE_CARE_LIBRARY.get(condition_key)
        if not entry:
            return None

        clean_species = (species or "any").lower().strip()
        data = dict(entry)

        # Apply species specialization if available
        if clean_species in ("cat", "dog"):
            specific_note = entry.get("species_notes", {}).get(clean_species)
            if specific_note:
                data["active_species_note"] = specific_note

        return data

    @classmethod
    def identify_matching_conditions(
        cls, symptoms_list: List[Dict[str, Any]], species: str = "any"
    ) -> List[str]:
        """Map reported symptoms to library condition keys."""
        matched_keys: List[str] = []
        clean_species = (species or "").lower().strip()

        for s in symptoms_list:
            s_name = (s.get("name") or "").lower().strip()

            if any(term in s_name for term in ["vomit", "emesis", "diarrhea", "stool", "watery"]):
                if "vomiting_diarrhea" not in matched_keys:
                    matched_keys.append("vomiting_diarrhea")

            if any(term in s_name for term in ["appetite", "eating", "food refusal", "anorexia"]):
                if "reduced_appetite" not in matched_keys:
                    matched_keys.append("reduced_appetite")

            if any(term in s_name for term in ["breath", "wheez", "cough", "panting", "dyspnea"]):
                if "difficulty_breathing" not in matched_keys:
                    matched_keys.append("difficulty_breathing")

            if any(term in s_name for term in ["seizure", "convuls", "tremor", "collaps", "unconscious"]):
                if "seizures_collapse" not in matched_keys:
                    matched_keys.append("seizures_collapse")

            if any(term in s_name for term in ["urina", "pee", "litter", "straining", "bladder"]):
                if "difficulty_urinating" not in matched_keys:
                    matched_keys.append("difficulty_urinating")

            if any(term in s_name for term in ["poison", "toxic", "chocolate", "lily", "chemical"]):
                if "poisoning" not in matched_keys:
                    matched_keys.append("poisoning")

            if any(term in s_name for term in ["limp", "lame", "leg", "sprain", "bone", "fracture"]):
                if "limping_injury" not in matched_keys:
                    matched_keys.append("limping_injury")

            if any(term in s_name for term in ["itch", "scratch", "skin", "redness", "rash"]):
                if "skin_irritation_itching" not in matched_keys:
                    matched_keys.append("skin_irritation_itching")

            if any(term in s_name for term in ["wound", "cut", "scratch", "bite", "scrape"]):
                if "minor_wounds" not in matched_keys:
                    matched_keys.append("minor_wounds")

            if any(term in s_name for term in ["heat", "sun", "hypertherm", "hot car"]):
                if "heat_exposure" not in matched_keys:
                    matched_keys.append("heat_exposure")

            if any(term in s_name for term in ["eye", "cornea", "squint", "discharge"]):
                if "eye_irritation" not in matched_keys:
                    matched_keys.append("eye_irritation")

            if any(term in s_name for term in ["behaviour", "behavior", "letharg", "energy", "hid"]):
                if "behavior_energy_changes" not in matched_keys:
                    matched_keys.append("behavior_energy_changes")

        return matched_keys

    @classmethod
    def synthesize_guide(
        cls,
        assessment_data: Dict[str, Any],
        pet_data: Dict[str, Any],
        risk_analysis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Synthesize tailored, evidence-based AI Pet Care Guide enforcing safety rules.

        Safety Principles:
        1. Emergency Primacy: Red-flag triggers lock urgency to EMERGENCY regardless of other inputs.
        2. Strict Contraindications: Never advise human medicines, forced feeding, or induced vomiting.
        3. Species Differentiation: Separate canine vs feline life-safety protocols.
        4. Uncertainty Preservation: Missing facts remain unknown.
        """
        now = datetime.now(timezone.utc)
        species = (pet_data.get("species") or "Unknown").strip()
        clean_species = species.lower()

        symptoms = assessment_data.get("symptoms") or []
        observations = assessment_data.get("observations") or {}
        follow_ups = assessment_data.get("follow_up_findings") or []
        risk_data = risk_analysis or assessment_data.get("risk_analysis") or {}

        risk_level = (risk_data.get("risk_level") or "LOW").upper()
        risk_score = risk_data.get("risk_score", 0)
        is_emergency = bool(risk_data.get("is_emergency", False))

        # 1. Identify matched condition keys
        matched_keys = cls.identify_matching_conditions(symptoms, clean_species)

        # Fallback if no specific condition matched
        if not matched_keys:
            matched_keys = ["behavior_energy_changes"]

        # 2. Check for hard-stop emergency triggers
        has_feline_urinary = clean_species == "cat" and "difficulty_urinating" in matched_keys
        has_critical_condition = any(
            k in matched_keys
            for k in ["difficulty_breathing", "seizures_collapse", "poisoning", "heat_exposure"]
        )
        has_critical_observation = (
            observations.get("breathing_change") in ["labored", "rapid", "very_heavy"]
            or observations.get("pain_observed") in ["severe", "extreme", "crying"]
        )

        overall_emergency = (
            is_emergency
            or risk_level == "EMERGENCY"
            or has_feline_urinary
            or has_critical_condition
            or has_critical_observation
        )

        # Determine Urgency Classification (4 levels per spec)
        if overall_emergency:
            urgency_classification = "EMERGENCY"
            urgency_label = "Emergency — Seek Immediate Veterinary Care"
            urgency_icon = "🚨"
            urgency_action_text = "Transport pet to an open emergency veterinary hospital immediately."
            urgency_timeline = "Immediate (< 1 hour)"
        elif risk_level == "HIGH":
            urgency_classification = "URGENT"
            urgency_label = "Urgent — Contact Veterinarian Promptly"
            urgency_icon = "⚠️"
            urgency_action_text = "Contact your veterinary clinic or urgent care service today."
            urgency_timeline = "Within 6-12 hours"
        elif risk_level == "MODERATE" or len(symptoms) > 1:
            urgency_classification = "APPOINTMENT_RECOMMENDED"
            urgency_label = "Veterinary Appointment Recommended"
            urgency_icon = "📅"
            urgency_action_text = "Schedule a clinical examination with your regular veterinarian."
            urgency_timeline = "Within 24-48 hours"
        else:
            urgency_classification = "HOME_MONITORING_REASONABLE"
            urgency_label = "Home Monitoring May Be Reasonable"
            urgency_icon = "ℹ️"
            urgency_action_text = "Follow low-risk comfort measures and observe closely for any changes."
            urgency_timeline = "Monitor for 12-24 hours"

        # 3. Assemble Section A: What to do now (Ordered, practical, low-risk)
        what_to_do_steps: List[Dict[str, Any]] = []
        step_num = 1

        if overall_emergency:
            what_to_do_steps.append({
                "step": step_num,
                "title": "Initiate Emergency Transport Protocol",
                "instruction": "Call the nearest emergency veterinary hospital to notify them of your arrival, and prepare safe, cushioned transport.",
                "is_critical": True,
            })
            step_num += 1

        for k in matched_keys:
            entry = IMMEDIATE_CARE_LIBRARY.get(k)
            if entry:
                for action in entry.get("what_to_do_now", [])[:2]:
                    if not any(s["instruction"] == action for s in what_to_do_steps):
                        what_to_do_steps.append({
                            "step": step_num,
                            "title": f"Comfort Measure ({entry['title']})",
                            "instruction": action,
                            "is_critical": False,
                        })
                        step_num += 1

        # 4. Assemble Section B: What NOT to do (Strict contraindications)
        what_to_avoid_items: List[Dict[str, Any]] = [
            {
                "rule": "Never Administer Human Pain Medications",
                "detail": "Paracetamol/Tylenol, Ibuprofen/Advil, and Aspirin are lethal to pets and cause rapid organ failure.",
                "severity": "CRITICAL",
            },
            {
                "rule": "Never Induce Vomiting Without Toxicologist Command",
                "detail": "Inducing vomiting for caustic chemicals or in disoriented pets causes fatal esophageal burning and aspiration pneumonia.",
                "severity": "CRITICAL",
            },
            {
                "rule": "Never Force-Feed Liquids or Food",
                "detail": "Do not syringe water or food into an unwilling, nauseous, or lethargic pet's mouth.",
                "severity": "HIGH",
            },
        ]

        for k in matched_keys:
            entry = IMMEDIATE_CARE_LIBRARY.get(k)
            if entry:
                for avoid in entry.get("what_to_avoid", [])[:2]:
                    if not any(avoid in item["detail"] for item in what_to_avoid_items):
                        what_to_avoid_items.append({
                            "rule": f"Prohibited ({entry['title']})",
                            "detail": avoid,
                            "severity": "HIGH",
                        })

        # 5. Assemble Section C: What to monitor (Specific deterioration triggers)
        monitoring_indicators: List[str] = [
            "Gum color: check that gums remain moist and pink (pale, white, blue, or yellow gums indicate shock).",
            "Energy level: note any progression from mild tiredness into deep lethargy or unresponsiveness.",
            "Hydration and fluid retention: watch for inability to keep water down or rapid fluid loss.",
        ]

        for k in matched_keys:
            entry = IMMEDIATE_CARE_LIBRARY.get(k)
            if entry:
                for item in entry.get("what_to_monitor", []):
                    if item not in monitoring_indicators:
                        monitoring_indicators.append(item)

        # 6. Assemble Section D: When to seek veterinary care (Urgency & thresholds)
        when_to_seek_care = {
            "urgency_classification": urgency_classification,
            "urgency_label": urgency_label,
            "urgency_icon": urgency_icon,
            "timeline": urgency_timeline,
            "action_recommendation": urgency_action_text,
            "emergency_escalation_criteria": [
                "Severe difficulty breathing, extended neck, or open-mouth breathing (especially cats).",
                "Sudden collapse, unresponsiveness, or seizure lasting longer than 3 minutes.",
                "Straining to urinate with little or no urine produced (critical in cats).",
                "Known or suspected ingestion of toxic chemicals, lilies, rodenticides, or chocolate.",
                "Pale, grey, or blue gums, hypothermia, or continuous bleeding.",
            ],
            "cutoff_instruction": (
                "If ANY emergency escalation criteria are observed, HOME MONITORING MUST STOP IMMEDIATELY. "
                "Transport your pet to the nearest emergency clinic without waiting."
            ),
        }

        # 7. Assemble Section E: Why this guidance is shown (Transparent clinical reasoning)
        sym_names = [s.get("name") for s in symptoms if s.get("name")]
        rationale_factors: List[Dict[str, Any]] = [
            {
                "category": "Reported Symptoms",
                "finding": f"{len(symptoms)} symptom(s) recorded: {', '.join(sym_names) or 'General check'}",
                "impact": f"Determined guidance categories: {', '.join([IMMEDIATE_CARE_LIBRARY.get(k, {}).get('title', k) for k in matched_keys])}",
            },
        ]

        if overall_emergency:
            rationale_factors.insert(0, {
                "category": "Life-Safety Emergency Priority",
                "finding": "Acute red-flag clinical indicator detected",
                "impact": "Locked triage urgency to EMERGENCY; overriding routine home-care scoring.",
            })

        # Include uncertainty and missing info notes
        uncertainty_notes: List[str] = []
        if not assessment_data.get("observations"):
            uncertainty_notes.append("No clinical observations recorded; normal vital status cannot be verified.")
        if not follow_ups:
            uncertainty_notes.append("Adaptive follow-up questions were unrecorded; fine-grained symptom history is incomplete.")
        if clean_species not in ["dog", "cat"]:
            uncertainty_notes.append(f"Species '{species}' has limited species-specific first aid literature; advise direct veterinary consult.")

        # 8. Veterinary Handoff Summary
        handoff_summary = {
            "patient": f"{pet_data.get('name', 'Pet')} ({species}, {pet_data.get('breed', 'Mixed')}, {pet_data.get('age', 'Unknown')} yrs)",
            "urgency": urgency_classification,
            "reported_symptoms": [
                f"{s.get('name')} (Severity: {s.get('severity', 'moderate')}, Duration: {s.get('duration_display') or s.get('duration') or 'Unspecified'})"
                for s in symptoms
            ],
            "medical_history": {
                "allergies": pet_data.get("allergies") or "None reported",
                "existing_conditions": pet_data.get("existing_conditions") or "None reported",
                "current_medications": pet_data.get("current_medications") or "None reported",
            },
            "vet_prep_checklist": [
                "Bring exact packaging, container, or plant sample if toxin exposure is suspected.",
                "Take photos/video of abnormal breathing, limping gait, or seizure on your phone.",
                "Safely collect stool or urine sample in clean container if voided naturally.",
                "Keep pet warm in a secure, well-ventilated carrier or crate with familiar towels.",
            ],
        }

        # 9. Real Emergency Care Protocols (Night & Holiday Support)
        after_hours_guidance = {
            "title": "Find Emergency Veterinary Care",
            "situation_notice": "If your primary veterinary clinic is closed at night, on weekends, or during holidays:",
            "verified_resources": [
                {
                    "name": "ASPCA Animal Poison Control Center (24/7)",
                    "phone": "(888) 426-4435",
                    "notes": "Available 24 hours a day, 365 days a year across North America.",
                },
                {
                    "name": "Pet Poison Helpline (24/7)",
                    "phone": "(855) 764-7661",
                    "notes": "24/7 veterinary toxicology support.",
                },
                {
                    "name": "AAHA Accredited Hospital Locator",
                    "url": "https://www.aaha.org/your-pet/find-a-vet/",
                    "notes": "Locate 24-hour certified emergency veterinary hospitals.",
                },
            ],
            "safe_search_instructions": (
                "Search your phone map for '24 hour emergency vet near me'. "
                "Always call the emergency hospital while on the way so their clinical triage "
                "team can prepare an oxygen cage, warmers, or immediate emergency stabilization."
            ),
            "no_wait_rule": "DO NOT wait until morning if your pet exhibits difficulty breathing, collapse, seizures, suspected poisoning, or inability to urinate.",
        }

        # 10. Collect verified evidence citations
        evidence_citations: List[Dict[str, Any]] = []
        for k in matched_keys:
            entry = IMMEDIATE_CARE_LIBRARY.get(k)
            if entry:
                for src in entry.get("evidence_sources", []):
                    if not any(c.get("title") == src.get("title") for c in evidence_citations):
                        evidence_citations.append(src)

        # Final structured payload
        return {
            "id": str(uuid.uuid4()),
            "title": "AI Pet Care Guide",
            "subtitle": "Understand what you can safely do now, what to avoid, and when your pet needs urgent veterinary care.",
            "generated_at": now.isoformat(),
            "species": species,
            "pet_name": pet_data.get("name", "Pet"),
            "urgency": {
                "classification": urgency_classification,
                "label": urgency_label,
                "icon": urgency_icon,
                "timeline": urgency_timeline,
                "action": urgency_action_text,
            },
            "section_a_what_to_do_now": what_to_do_steps,
            "section_b_what_to_avoid": what_to_avoid_items,
            "section_c_what_to_monitor": monitoring_indicators,
            "section_d_when_to_seek_care": when_to_seek_care,
            "section_e_why_shown": {
                "rationale_factors": rationale_factors,
                "uncertainty_and_missing_data": uncertainty_notes,
                "matched_conditions": matched_keys,
            },
            "veterinary_handoff": handoff_summary,
            "emergency_after_hours": after_hours_guidance,
            "evidence_sources": evidence_citations,
            "disclaimer": cls.STANDARD_DISCLAIMER,
        }

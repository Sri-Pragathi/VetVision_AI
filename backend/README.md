# VetVision AI — Backend Foundation & Health Assessment Architecture

> **AI-Powered Pet Health Early Warning & Veterinary Assistance System**  
> University Innovation & Technology Competition Project

---

## 1. Overview & Vision

**VetVision AI** is an intelligent veterinary assistance and pet health platform engineered to empower pet owners and veterinary professionals with early detection of diseases, health risks, and acute emergencies. By bridging clinical triage principles with modern software architecture, the system provides automated symptom assessment, multi-pet tracking, risk scoring, and structured veterinary reporting.

This repository hosts the **Backend Foundation and Health Assessment Architecture**, providing the secure, modular, enterprise-grade RESTful API upon which all subsequent AI analysis, image diagnosis, and emergency triage pipelines are built.

---

## 2. Backend Architecture

The backend adheres to a clean, decoupled **Layered Modular Architecture** leveraging Flask's Application Factory pattern:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              HTTP Clients                               │
│                      (Web / Mobile / Third-Party)                       │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ JSON / REST (v1)
┌────────────────────────────────────▼────────────────────────────────────┐
│                           API Routing Layer                             │
│   /auth        /users        /pets        /assessments      /symptoms   │
└───────────────┬──────────────────────────────────────────┬──────────────┘
                │                                          │
┌───────────────▼─────────────┐            ┌───────────────▼──────────────┐
│ Validation & Serialization  │            │  Authentication & Security   │
│        (Marshmallow)        │            │   (JWT-Extended & bcrypt)    │
└───────────────┬─────────────┘            └───────────────┬──────────────┘
                │                                          │
┌───────────────▼──────────────────────────────────────────▼──────────────┐
│                             Service Layer                               │
│ (AuthService, UserService, PetService, AssessmentService, SymptomService│
│           AiDataPreparationService, EmergencyAssessmentService)          │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                      Data Access & Models Layer                         │
│  User, Pet, TokenBlocklist, Symptom, HealthAssessment, AssessmentSymptom│
│                   HealthObservation, AssessmentNote                     │
│                     (SQLAlchemy 2.0 ORM + Alembic)                      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                            Database Engine                              │
│                 PostgreSQL (Production) / SQLite (Dev)                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Database Models & Entity-Relationship Design

```
USER (1) ──────────< (Many) PET (1) ──────────< (Many) HEALTH ASSESSMENT
                                                              │
                     ┌────────────────────────────────────────┼──────────────────────────────────┐
                     │ (1 to Many)                            │ (1 to 1)                         │ (1 to Many)
                     ▼                                        ▼                                  ▼
             ASSESSMENT SYMPTOM                      HEALTH OBSERVATION                   ASSESSMENT NOTE
             (Links to SYMPTOM)                      (Physiological Metrics)              (Free-text clinical notes)
```

### Models

1. **`User`**:
   - `id`: UUID (String 36, Primary Key)
   - `name`: String(100), not null
   - `email`: String(255), unique, indexed, not null
   - `password_hash`: String(255), securely hashed with bcrypt (12 rounds)
   - `created_at`, `updated_at`: UTC timestamps
   - Relationships: One-to-many with `Pet` (`cascade="all, delete-orphan"`)

2. **`Pet`**:
   - `id`: UUID (String 36, Primary Key)
   - `owner_id`: ForeignKey to `User.id` (`ondelete="CASCADE"`), indexed
   - `name`, `species`: String, required
   - `breed`, `sex`, `date_of_birth`: Optional demographics (with calculated `@property age`)
   - `weight`, `allergies`, `existing_conditions`, `current_medications`, `vaccination_status`: Clinical baseline
   - Relationships: Belongs to `User`, One-to-many with `HealthAssessment` (`cascade="all, delete-orphan"`)

3. **`Symptom`** (Standardized Clinical Vocabulary):
   - `id`: UUID (String 36, Primary Key)
   - `name`: String(100), unique, indexed (e.g., `vomiting`, `difficulty breathing`, `itching`)
   - `category`: String(50), indexed (`Digestive`, `Respiratory`, `Skin`, `Eyes`, `Ears`, `Neurological`, `Musculoskeletal`, `Urinary`, `Behavioural`, `General`)
   - `description`: Text
   - Auto-seeded with 20 clinical symptom categories.

4. **`HealthAssessment`**:
   - `id`: UUID (String 36, Primary Key)
   - `pet_id`: ForeignKey to `Pet.id` (`ondelete="CASCADE"`), indexed
   - `status`: String(20) (`in_progress`, `completed`, `cancelled`)
   - `started_at`: UTC timestamp, required
   - `completed_at`: UTC timestamp, set upon completion
   - Relationships: One-to-many `AssessmentSymptom`, One-to-one `HealthObservation`, One-to-many `AssessmentNote`

5. **`AssessmentSymptom`**:
   - `id`: UUID (String 36, Primary Key)
   - `assessment_id`: ForeignKey to `HealthAssessment.id`
   - `symptom_id`: ForeignKey to `Symptom.id`
   - `severity`: String (`mild`, `moderate`, `severe`)
   - `duration_value`: Float (> 0)
   - `duration_unit`: String (`hours`, `days`, `weeks`, `months`)
   - `notes`: Text

6. **`HealthObservation`**:
   - `id`: UUID (String 36, Primary Key)
   - `assessment_id`: ForeignKey to `HealthAssessment.id`, unique
   - Controlled vocabulary fields: `appetite`, `water_intake`, `activity_level`, `behaviour_change`, `sleep_change`, `stool_change`, `urine_change`, `breathing_change`, `pain_observed`

7. **`AssessmentNote`**:
   - `id`: UUID (String 36, Primary Key)
   - `assessment_id`: ForeignKey to `HealthAssessment.id`
   - `note`: Text (up to 5,000 chars)

8. **`TokenBlocklist`**:
   - `id`: Integer Primary Key
   - `jti`: String(36), indexed
   - `token_type`: String(10) (`access` or `refresh`)

---

## 4. Assessment Lifecycle Management

Health assessments follow a strict state machine:

```
                  ┌──────────────┐
                  │   STARTED    │
                  └──────┬───────┘
                         │ (auto)
                         ▼
                  ┌──────────────┐
                  │ IN_PROGRESS  │
                  └──────┬───────┘
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
  ┌──────────────┐                ┌──────────────┐
  │  COMPLETED   │                │  CANCELLED   │
  └──────────────┘                └──────────────┘
```

- An assessment begins in `in_progress`.
- It can transition from `in_progress` → `completed` (sets `completed_at` timestamp).
- It can transition from `in_progress` → `cancelled`.
- **Invalid transitions** (e.g., `completed` → `in_progress` or `cancelled` → `completed`) are blocked with HTTP `422 Unprocessable Entity`.

---

## 5. Multi-Tenant Ownership Security

Every health assessment and pet is protected by strict ownership isolation:

$$\text{User} \longrightarrow \text{Pet} \longrightarrow \text{HealthAssessment}$$

- **Zero Cross-User Access**: A logged-in user cannot view, modify, or delete another user's pet or assessment.
- **Cross-User Creation Blocked**: Attempting to create an assessment for a pet owned by someone else returns HTTP `403 Forbidden`.
- **No ID Enumeration**: Access is gated before any database modification occurs.

---

## 6. Complete API Reference (`/api/v1/`)

All requests and responses use JSON and the standard response structure:

```json
// Success
{ "success": true, "message": "...", "data": { ... } }

// Error
{ "success": false, "message": "...", "errors": { ... } }
```

### 1. System Health
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/health` | None | Verify backend service availability |

### 2. Authentication (`/api/v1/auth`)
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | None | Register new user account |
| `POST` | `/api/v1/auth/login` | None | Receive `access_token` and `refresh_token` |
| `POST` | `/api/v1/auth/refresh` | Refresh JWT | Exchange refresh token for fresh access token |
| `POST` | `/api/v1/auth/logout` | JWT | Add token to revocation blocklist |
| `GET` | `/api/v1/auth/me` | Access JWT | Retrieve authenticated user profile |

### 3. User Profile (`/api/v1/users`)
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/users/me` | Access JWT | Retrieve user profile |
| `PUT` | `/api/v1/users/me` | Access JWT | Update `name` or `email` |

### 4. Pet Management (`/api/v1/pets`)
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/pets` | Access JWT | Register pet under current user |
| `GET` | `/api/v1/pets` | Access JWT | List all pets owned by current user |
| `GET` | `/api/v1/pets/<pet_id>` | Access JWT | Get pet details (ownership enforced) |
| `PUT` | `/api/v1/pets/<pet_id>` | Access JWT | Update pet profile (ownership enforced) |
| `DELETE` | `/api/v1/pets/<pet_id>` | Access JWT | Delete pet (ownership enforced) |

### 5. Symptoms Vocabulary (`/api/v1/symptoms`)
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/symptoms` | None / JWT | List all clinical symptoms |
| `GET` | `/api/v1/symptoms?category=Skin` | None / JWT | Filter symptoms by category (case-insensitive) |

### 6. Health Assessments (`/api/v1/assessments` & `/api/v1/pets/<pet_id>/assessments`)
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/pets/<pet_id>/assessments` | Access JWT | Start new health assessment session |
| `GET` | `/api/v1/pets/<pet_id>/assessments` | Access JWT | List all assessments for that pet |
| `GET` | `/api/v1/assessments/<assessment_id>` | Access JWT | Retrieve assessment details |
| `PUT` | `/api/v1/assessments/<assessment_id>` | Access JWT | Update status (`completed`, `cancelled`) |
| `DELETE` | `/api/v1/assessments/<assessment_id>` | Access JWT | Delete assessment session |
| `POST` | `/api/v1/assessments/<assessment_id>/symptoms` | Access JWT | Attach symptom (severity, duration) |
| `PUT` | `/api/v1/assessments/<assessment_id>/symptoms/<symptom_id>` | Access JWT | Update attached symptom details |
| `DELETE` | `/api/v1/assessments/<assessment_id>/symptoms/<symptom_id>` | Access JWT | Remove symptom from assessment |
| `PUT` | `/api/v1/assessments/<assessment_id>/observations` | Access JWT | Upsert structured observations |
| `POST` | `/api/v1/assessments/<assessment_id>/notes` | Access JWT | Append free-text clinical note |
| `GET` | `/api/v1/assessments/<assessment_id>/ai-data` | Access JWT | Retrieve formatted AI-ready payload & emergency screening |

---

## 7. Sample API Requests & Responses

### A. Start an Assessment
`POST /api/v1/pets/2634ab02-952d-4301-a807-4cd0af09c2d2/assessments`

**Response (`201 Created`):**
```json
{
  "success": true,
  "message": "Health assessment session started successfully",
  "data": {
    "id": "7b8d4f12-098e-4a6c-941e-61cf6f8d3820",
    "pet_id": "2634ab02-952d-4301-a807-4cd0af09c2d2",
    "status": "in_progress",
    "started_at": "2026-10-05T18:25:00.000000Z",
    "completed_at": null,
    "symptoms": [],
    "observations": null,
    "notes": []
  }
}
```

### B. Add a Symptom
`POST /api/v1/assessments/7b8d4f12-098e-4a6c-941e-61cf6f8d3820/symptoms`
```json
{
  "symptom_id": "d0e1f2a3-b4c5-6789-0123-abcdef012345",
  "severity": "severe",
  "duration_value": 3,
  "duration_unit": "days",
  "notes": "Labored breathing at rest"
}
```

### C. Record Structured Observations
`PUT /api/v1/assessments/7b8d4f12-098e-4a6c-941e-61cf6f8d3820/observations`
```json
{
  "appetite": "decreased",
  "water_intake": "excessive",
  "activity_level": "lethargic",
  "breathing_change": "labored",
  "pain_observed": "severe"
}
```

---

## 8. AI-Ready Data Format

The `AiDataPreparationService` standardizes and cleanses assessment data into a normalized object ready for future inference pipelines:

```json
{
  "pet": {
    "species": "Canine",
    "breed": "German Shepherd",
    "age": 4,
    "sex": "Male Neutered",
    "weight": 34.0,
    "allergies": "Chicken",
    "existing_conditions": "Hip dysplasia",
    "current_medications": "Glucosamine"
  },
  "symptoms": [
    {
      "name": "difficulty breathing",
      "category": "Respiratory",
      "severity": "severe",
      "duration": {
        "value": 3.0,
        "unit": "days"
      },
      "notes": "Labored breathing at rest"
    }
  ],
  "observations": {
    "appetite": "decreased",
    "water_intake": "excessive",
    "activity_level": "lethargic",
    "behaviour_change": null,
    "sleep_change": null,
    "stool_change": null,
    "urine_change": null,
    "breathing_change": "labored",
    "pain_observed": "severe"
  },
  "additional_notes": "Pet is reluctant to lie down."
}
```

---

## 9. Emergency Triage Screening Interface

The `EmergencyAssessmentService` provides an initial computational safety layer:
- Identifies critical flags (e.g. `difficulty breathing`, `seizures`, `severe` pain).
- Assigns priority risk levels: `routine`, `urgent`, `emergency`.
- Includes mandatory clinical safety disclaimers: *Assistive computational screening only; does not replace veterinary diagnosis.*

---

## 10. Running Tests & Code Coverage

```bash
cd backend

# Run all tests (Steps 1, 2, 3, 4, and 5)
.\venv\Scripts\pytest -v

# Run with coverage report
.\venv\Scripts\pytest --cov=app tests/
```

**Results (Step 5 Complete):**
- **107 / 108 tests passing** (1 skipped — text-type question format)
- **92% Code Coverage** across 2,510 statements
- **0 regressions** — all Step 1, 2, 3, and 4 tests continue to pass.

---

## 11. Step 3 — Dynamic Symptom & Follow-Up Question Engine

### Overview

The Dynamic Question Engine extends the health assessment system with intelligent, context-aware follow-up questions. When a user selects a symptom such as *Vomiting*, the system automatically prioritizes relevant clinical questions:

> *"How many times has your pet vomited?"*
> *"Is there blood present in the vomit?"*
> *"Is your pet able to keep water down?"*

Emergency symptoms such as *"Difficulty breathing"* or *"Seizures"* cause `priority=emergency` questions to surface **first**, before routine queries.

---

### New Models (Step 3)

#### `FollowUpQuestion`
| Column | Type | Description |
|---|---|---|
| `id` | String(36) UUID | Primary key |
| `question_text` | Text | The clinical question text |
| `question_type` | String(30) | `yes_no`, `single_choice`, `multiple_choice`, `number`, `text` |
| `category` | String(50) | Symptom category (Digestive, Respiratory, etc.) |
| `priority` | String(20) | `emergency`, `high`, `medium`, `low` |
| `symptom_id` | FK → Symptom | Optional link to specific symptom |
| `species` | String(50) | Species restriction (`Canine`, `Feline`) or `NULL` = all species |
| `min_age_months` | Integer | Minimum pet age in months (optional) |
| `max_age_months` | Integer | Maximum pet age in months (optional) |
| `is_emergency_related` | Boolean | Surfaces before routine questions |
| `is_active` | Boolean | Soft-disable without deletion |

#### `FollowUpQuestionOption`
| Column | Type | Description |
|---|---|---|
| `id` | String(36) UUID | Primary key |
| `question_id` | FK → FollowUpQuestion | Parent question (CASCADE) |
| `option_text` | String(255) | Human-readable label |
| `option_value` | String(100) | Machine-readable value |
| `severity_weight` | Float (0.0–1.0) | Clinical significance score |
| `emergency_flag` | Boolean | Selecting this option triggers emergency warning |

#### `AssessmentAnswer`
| Column | Type | Description |
|---|---|---|
| `id` | String(36) UUID | Primary key |
| `assessment_id` | FK → HealthAssessment | Parent assessment (CASCADE) |
| `question_id` | FK → FollowUpQuestion | Answered question |
| `selected_option_id` | FK → FollowUpQuestionOption | For choice questions |
| `answer_text` | Text | For text questions |
| `numeric_value` | Float | For number questions |
| `boolean_value` | Boolean | For yes/no questions |
| `triggered_emergency` | Boolean | Set if selected option had `emergency_flag=True` |
| **Unique** | `(assessment_id, question_id)` | One answer per question per assessment |

---

### Step 3 APIs

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/questions` | Public | Browse question bank (filter: `category`, `priority`, `species`, `symptom_id`) |
| `GET` | `/api/v1/assessments/<id>/next-questions` | JWT | Context-aware next batch (param: `batch_size`) |
| `POST` | `/api/v1/assessments/<id>/answers` | JWT | Submit answer to a question |
| `GET` | `/api/v1/assessments/<id>/answers` | JWT | Retrieve all submitted answers |
| `GET` | `/api/v1/assessments/<id>/question-state` | JWT | Progress, emergency flags, readiness |

---

### Dynamic Question Engine Rules

1. **Emergency First** — `priority=emergency` questions always surface before all others.
2. **Symptom Context** — Only questions linked to selected symptoms or their categories are returned.
3. **Species Awareness** — `species=Canine` questions excluded for Feline pets and vice versa.
4. **Age Awareness** — Questions with `min_age_months`/`max_age_months` are filtered by pet's calculated age.
5. **Already-Answered Exclusion** — Answered questions never repeat.
6. **Conditional Triggers** — Certain `option_value`s (e.g. `blood_yes`, `gums_blue`) unlock additional question categories.
7. **Emergency Propagation** — Selecting `emergency_flag=True` option sets `triggered_emergency=True` and appears in question-state flags.

---

### Question Bank

Seeded with **200+ evidence-informed clinical questions** across all 10 symptom categories:

| Category | Priority | Sample Question |
|---|---|---|
| Respiratory | emergency | "Is your pet currently struggling to breathe?" |
| Neurological | emergency | "Is your pet currently having a seizure?" |
| Urinary | emergency | "Is your pet straining to urinate with little or no output?" |
| Digestive | high | "How many times has your pet vomited in the past 24 hours?" |
| Digestive | high | "Is there blood present in the vomit?" |
| Skin | medium | "Is your pet scratching constantly or intensely?" |
| Eyes | medium | "Is there visible discharge from one or both eyes?" |
| General | medium | "Has your pet's appetite changed noticeably?" |
| Behavioural | low | "Is your pet hiding or withdrawing from interaction?" |

---

### Database Migration (Step 3)

Migration: `migrations/versions/37f1877f260e_add_step_3_follow_up_questions_*`

Creates:
- `follow_up_questions` (indexes: `category`, `symptom_id`)
- `follow_up_question_options` (index: `question_id`)
- `assessment_answers` (indexes: `assessment_id`, `question_id`, unique constraint)

```bash
flask db upgrade
```

---

### AI Integration

`AiDataPreparationService` now includes follow-up Q&A in the AI-ready payload:

```json
{
  "pet": { "species": "Canine", "age": "4 years" },
  "symptoms": [{ "name": "vomiting", "severity": "moderate" }],
  "observations": { "appetite": "decreased" },
  "additional_notes": "Pet is reluctant to drink.",
  "follow_up_answers": [
    {
      "question": "How many times has your pet vomited in the past 24 hours?",
      "category": "Digestive",
      "priority": "high",
      "is_emergency_related": false,
      "answer_option": "More than 5 times",
      "severity_weight": 0.9,
      "triggered_emergency": false
    }
  ]
}
```

---

### Medical Safety Notice

> **VetVision AI is an early health assessment support tool only.**
> It does **NOT** diagnose diseases or replace professional veterinary care.
> Emergency indicators recommend immediate veterinary attention.
> Every question-state response includes a mandatory safety disclaimer.

---

## 12. Step 4 — AI Health Risk Analysis Engine

### Overview

Step 4 implements an **explainable, transparent pet health risk analysis engine** designed with an **ML-ready pluggable architecture**. The engine evaluates multi-modal data collected across Steps 1–3:
- **Pet Demographics & History** — species, calculated age, developmental vulnerabilities (juvenile / senior), existing conditions, allergies.
- **Symptom Manifestations** — clinical severity (`mild`, `moderate`, `severe`), duration progression (normalized to hours/days), co-occurrence.
- **Physiological & Behavioral Observations** — appetite, dehydration risks, activity depression, respiratory effort, pain signs, elimination abnormalities.
- **Dynamic Follow-Up Q&A** — clinical weights from user answers, indicators of worsening condition.
- **Emergency Triage Indicators** — hard-stop prioritization for acute life-threatening situations.

### Pluggable Architecture (`BaseRiskAnalysisEngine`)

```
┌────────────────────────────────────────────────────────┐
│               AiDataPreparationService                 │
│         (Normalizes Steps 1–3 Clinical Data)           │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                  RiskAnalysisService                   │
│   (Ownership validation, state checks, persistence)    │
└───────────────────────────┬────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │  BaseRiskAnalysisEngine   │
              │     (Abstract Adapter)    │
              └─────────────┬─────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         ▼                                     ▼
┌─────────────────────────────────┐   ┌────────────────────────────────┐
│   RuleBasedRiskAnalysisEngine   │   │     Future ML Model Adapter    │
│  (Clinical Heuristic Scoring)   │   │   (PyTorch / ONNX / LightGBM)  │
│      Active Implementation      │   │    Drop-in without rewrites    │
└─────────────────────────────────┘   └────────────────────────────────┘
```

The system does **NOT** invent a trained AI model, fabricate accuracy percentages, or claim definitive veterinary disease diagnosis. It provides transparent clinical heuristic scoring via `RuleBasedRiskAnalysisEngine` while providing `BaseRiskAnalysisEngine` so trained veterinary ML models can be plugged in later with zero architectural rewrites.

---

### Risk Levels & Scoring Breakdown

| Risk Level | Score Range | Primary Recommendation |
|---|---|---|
| **LOW** | 0 – 29 | Routine home monitoring. Contact vet if symptoms persist beyond 48 hours. |
| **MODERATE** | 30 – 59 | Non-urgent veterinary examination recommended within 24–48 hours. |
| **HIGH** | 60 – 84 | Urgent veterinary evaluation recommended as soon as possible (same day). |
| **EMERGENCY** | 85 – 100 | Immediate emergency veterinary hospital attention required. Do not wait. |

### Emergency Hard-Stop Rule (Non-Downgrade Guarantee)

Emergency conditions are **never downgraded** even if other symptom counts are low.
If any of the following triggers are present:
1. Critical symptoms (`difficulty breathing`, `seizures`, `collapse`, `severe bleeding`, `unresponsiveness`) with moderate or severe severity.
2. Abnormal respiratory effort (`labored` or `wheezing` in observations).
3. Severe physical pain (`pain_observed == severe`).
4. Follow-up answer with an emergency flag (`emergency_flag == True` or `triggered_emergency == True`).

The engine **immediately enforces**:
- `risk_level = "EMERGENCY"`
- `risk_score = max(calculated_score, 90)` (floor of 90)
- `emergency = True` / `is_emergency = True`
- Emergency triggers featured prominently at the top of `key_factors`
- Clear emergency veterinary hospital warning

---

### Step 4 Database Model (`AssessmentRiskAnalysis`)

Table: `assessment_risk_analyses`  
Migration: `migrations/versions/f13704143945_add_step_4_assessment_risk_analyses_.py`

| Column | Type | Description |
|---|---|---|
| `id` | String(36) UUID | Primary key |
| `assessment_id` | FK → HealthAssessment | Unique 1-to-1 link (`CASCADE`), indexed |
| `risk_level` | String(20) | `LOW`, `MODERATE`, `HIGH`, `EMERGENCY` |
| `risk_score` | Integer | 0 to 100 normalized score |
| `key_factors` | JSON | Human-readable explanation factors (top drivers) |
| `factor_breakdown` | JSON | Sub-scores: symptoms, duration, observations, answers, vulnerability |
| `recommendation` | Text | Clinical action recommendation |
| `is_emergency` | Boolean | Emergency indicator flag |
| `engine_version` | String(50) | `v1.0.0-rule_hybrid` |
| `disclaimer` | Text | Mandatory veterinary safety disclaimer |
| `created_at` | DateTime(tz) | Timestamp generated |
| `updated_at` | DateTime(tz) | Timestamp updated |

---

### Step 4 APIs

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/assessments/<id>/risk-analysis` | JWT | Execute explainable risk analysis & persist result |
| `GET` | `/api/v1/assessments/<id>/risk-analysis` | JWT | Retrieve latest stored risk analysis result |

#### Sample API Response:

```json
{
  "status": "success",
  "message": "AI health risk analysis completed successfully",
  "data": {
    "id": "c620436d-b847-49d9-bbd1-dfa4c038481c",
    "assessment_id": "17a3d660-3893-465b-9745-c7e1e47cd22d",
    "risk_level": "HIGH",
    "risk_score": 72,
    "key_factors": [
      "Severe primary symptom: Diarrhea",
      "Symptoms persisting for several days (3–7 days)",
      "Complete loss of appetite / anorexia",
      "Noticeable lethargy and sluggishness",
      "Follow-up response indicates worsening clinical condition"
    ],
    "factor_breakdown": {
      "symptom_score": 45,
      "duration_score": 12,
      "observation_score": 24,
      "follow_up_score": 11,
      "vulnerability_modifier": 0,
      "emergency_override": false,
      "raw_calculated_score": 92
    },
    "recommendation": "Urgent veterinary evaluation recommended as soon as possible (same day). Monitor pet closely and do not leave unattended.",
    "emergency": false,
    "is_emergency": false,
    "engine_version": "v1.0.0-rule_hybrid",
    "disclaimer": "This assessment is for early-warning support and does not replace professional veterinary diagnosis. If your pet is in acute distress, contact an emergency veterinary hospital immediately.",
    "created_at": "2026-10-08T15:00:00+00:00",
    "updated_at": "2026-10-08T15:00:00+00:00"
  }
}
```

---

---

## 13. Step 5 — Computer Vision / Pet Image Analysis Pipeline

### Overview

Step 5 implements a **secure, explainable Computer Vision pipeline** allowing pet owners and clinical staff to attach pet photographs to health assessments and extract structured visual observations.

```
Pet Profile
    ↓
Health Assessment
    ↓
Symptoms + Observations
    ↓
Dynamic Follow-up Questions
    ↓
Risk Analysis (Step 4)
    ↓
Pet Image Upload & Validation
    ↓
Computer Vision Quality Gate & Analysis
    ↓
Visual Observations Extraction
    ↓
Combined AI Assessment / Risk Re-analysis
```

### Pluggable Architecture

1. **Storage Abstraction (`BaseImageStorage` / `LocalStorageService`)**
   - Decoupled from physical disk layouts.
   - Prevents path-traversal attacks by verifying canonical path prefixes.
   - Generates safe UUID-based storage keys (`assessments/<id>/<uuid>.<ext>`).
   - Allows seamless drop-in replacement with cloud object storage (e.g. AWS S3, Google Cloud Storage, Azure Blob).

2. **Computer Vision Abstraction (`BaseImageAnalysisEngine` / `BasicImageAnalysisEngine`)**
   - Clean adapter contract (`BaseImageAnalysisEngine.analyze_image(...) -> ImageAnalysisOutput`).
   - Standardized output structure with quality metrics, visual observations, and recommendations.
   - Supports future integration of trained veterinary deep learning models (e.g. PyTorch, YOLOv8, ONNX lesion segmentation) without altering API routes, schemas, or database models.

3. **Image Quality Gate**
   - Evaluates:
     - **Resolution:** Gated at minimum 150x150 px.
     - **Lighting/Luminance:** Detects underexposed (< 35 luminance) and washed-out overexposed (> 240 luminance) images.
     - **Contrast:** Gated at minimum standard deviation of 12.0.
     - **Sharpness/Blur:** High-frequency edge density evaluation.
   - If an image fails the quality gate:
     - Status: `REQUIRES_BETTER_IMAGE`
     - Returns actionable guidance (e.g. *"Insufficient lighting"*, *"Image resolution is too low"*).
     - Does **NOT** draw medical conclusions from poor-quality images.

4. **Visual Observations Model (`ImageObservation`)**
   - Observations are strictly labeled as computer-vision observations rather than medical diagnoses:
     - `SUITABLE_FOR_ANALYSIS`: Adequate lighting, resolution, and contrast.
     - `POOR_IMAGE_QUALITY`: Insufficient lighting or focus.
     - `ELEVATED_ERYTHEMA_DETECTED`: Prominent localized red-channel concentration (dermatological context).
     - `STANDARD_COLOR_DISTRIBUTION`: Expected baseline coloration.

---

### Step 5 Database Models

#### `AssessmentImage` (`assessment_images`)
| Column | Type | Description |
|---|---|---|
| `id` | String(36) UUID | Primary key |
| `assessment_id` | FK → HealthAssessment | Parent assessment (`CASCADE`), indexed |
| `pet_id` | FK → Pet | Associated pet (`CASCADE`), indexed |
| `original_filename` | String(255) | Sanitized client filename |
| `storage_path` | String(500) | Relative storage object key |
| `mime_type` | String(100) | Validated MIME type (`image/jpeg`, `image/png`, `image/webp`) |
| `file_size` | Integer | Byte count |
| `width`, `height` | Integer | Pixel dimensions |
| `processing_status` | String(30) | `UPLOADED`, `READY`, `ANALYZING`, `ANALYZED`, `FAILED` |
| `analysis_status` | String(30) | `PENDING`, `ANALYZED`, `REQUIRES_BETTER_IMAGE`, `FAILED` |
| `quality_gate` | String(30) | `PASSED`, `REQUIRES_BETTER_IMAGE` |

#### `ImageObservation` (`image_observations`)
| Column | Type | Description |
|---|---|---|
| `id` | String(36) UUID | Primary key |
| `assessment_image_id` | FK → AssessmentImage | Parent image (`CASCADE`), indexed |
| `observation_type` | String(50) | `visual_quality`, `visual_feature`, `color_profile` |
| `observation_label` | String(100) | `SUITABLE_FOR_ANALYSIS`, `ELEVATED_ERYTHEMA_DETECTED`, etc. |
| `severity` | String(20) | `normal`, `mild`, `moderate`, `severe` |
| `region` | String(100) | `overall_image`, `focal_region` |
| `description` | Text | Human-readable explanation of visual feature |
| `source` | String(50) | `computer_vision` |
| `model_version` | String(50) | `v1.0.0-cv_baseline` |

---

### Step 5 APIs

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/assessments/<id>/images` | JWT | Upload pet photo (`multipart/form-data`, max 10MB) |
| `GET` | `/api/v1/assessments/<id>/images` | JWT | List all photos attached to an assessment |
| `GET` | `/api/v1/assessment-images/<id>` | JWT | Retrieve metadata and observation status for single photo |
| `POST` | `/api/v1/assessment-images/<id>/analyze` | JWT | Execute computer vision quality gating and observation extraction |
| `GET` | `/api/v1/assessment-images/<id>/analysis` | JWT | Retrieve structured CV observations and quality metrics |
| `DELETE` | `/api/v1/assessment-images/<id>` | JWT | Delete photo from storage and database (cascade cleanup) |

---

### Integration with Step 4 Risk Engine & Safety

1. **`AiDataPreparationService`:**
   - Injects `image_analysis` section into payload with `images_count`, `analyzed_count`, and structured visual observations.
2. **`RuleBasedRiskAnalysisEngine`:**
   - Consumes visual features safely (e.g. localized erythema adds correlated factor, maximum +8 points).
   - Image existence alone never artificially inflates risk score.
   - **Emergency conditions are NEVER downgraded** by attached images.
3. **Mandatory Clinical Safety Disclaimer:**
   > *"This image analysis provides computational computer-vision observations for early-warning support and does not replace professional veterinary examination or diagnosis."*

---

## 14. Step 6 — Veterinary Report & Explainable Health Summary

### Overview

Step 6 implements a clinical-grade, versioned **Veterinary Report & Explainable Health Summary** engine. The service gathers validated data across Steps 1 through 5 into an immutable, point-in-time clinical report snapshot suitable for:
1. **Pet Owner Review** — transparent explanation of findings, clear risk categories, and non-alarmist guidance.
2. **Veterinary Consultation / Handoff** — concise clinical brief that an owner can share with attending veterinary staff.
3. **Frontend Display & Future PDF Export** — semantic HTML rendering engine with print-ready styling and built-in XSS protection.
4. **Innovation Day Demonstration** — clear explainability breakdown showing *why* risk scores and triage priorities were assigned.

```
Health Assessment
       │
       ▼
Pet Demographics & Baseline Profile (Step 1)
       │
       ▼
Reported Symptoms, Severity & Chronicity (Step 2)
       │
       ▼
Physiological & Behavioral Observations (Step 2)
       │
       ▼
Dynamic Follow-Up Questions & Critical Answers (Step 3)
       │
       ▼
Computer Vision Image Analysis Observations (Step 5)
       │
       ▼
AI Health Risk Score & Factor Breakdown (Step 4)
       │
       ▼
Emergency Hard-Stop Screening Status (Step 2/4)
       │
       ▼
Clinical Recommendation & Veterinary Handoff Brief
       │
       ▼
Structured Snapshot (JSON) + Sanitized HTML Document
```

---

### Pluggable Architecture & Data Flow

- **Zero Duplicate Diagnostic Logic:** Reuses the verified output from Step 4 (`AssessmentRiskAnalysis`) and Step 5 (`AssessmentImage` & `ImageObservation`). It does not compute competing risk numbers or fabricate medical certainty.
- **Snapshot Immutability & Versioning:** Every report generation creates an immutable snapshot record. If assessment symptoms or observations change later, regenerating the report creates a new sequential version (`v1`, `v2`, `v3`...) and transitions historical reports to `ARCHIVED`, preserving an untampered audit trail.
- **XSS & Injection Protection:** User-supplied content (e.g. pet names, clinical notes, custom answers) is automatically escaped using `html.escape` to ensure that rendering to HTML is safe against script injection.

---

### The 13 Structured Report Sections

Each generated report contains a validated JSON payload (`report_data`) structured into 13 distinct sections:

1. **`metadata`** — Report UUID, version number, generation timestamp, generating user UUID, and system engine identifiers.
2. **`pet`** — Demographics without fabrication: name, species, breed, calculated age, sex, weight, allergies, existing conditions, medications, and vaccination status.
3. **`assessment`** — Assessment lifecycle status, creation date, completion timestamp, and notes.
4. **`symptoms`** — Array of clinical signs with symptom name, category, severity, duration value/unit/display, and notes.
5. **`follow_up_findings`** — Adaptive questions asked, recorded answers, selected options, priorities, and emergency triggers.
6. **`observations`** — Appetite, water intake, activity level, respiration change, pain signs, elimination, and sleep patterns.
7. **`image_analysis`** — Structured CV findings: image IDs, analysis status, quality gate verdict, quality warnings, and visual observations using cautious non-diagnostic language.
8. **`risk_analysis`** — Step 4 score (0–100), risk level (`LOW`, `MODERATE`, `HIGH`, `EMERGENCY`), key factors, factor breakdown, and engine version.
9. **`explainability`** — Multi-factor explanation breakdown showing exactly how symptoms, duration, observations, dynamic follow-up answers, and pet vulnerabilities contributed to the final score.
10. **`emergency`** — Emergency indicators status (`No emergency indicators identified`, `Urgent evaluation recommended`, `Emergency veterinary attention recommended`), boolean flags, and specific triggers.
11. **`recommendation`** — Clear triage action from the risk engine distinguishing routine monitoring, urgent evaluation, or immediate emergency hospital care.
12. **`veterinary_handoff`** — Concise clinical brief summarizing patient demographics, primary complaint, symptoms, observations, image notes, and recommended next steps for veterinary professionals.
13. **`disclaimer`** — Prominent legal and clinical medical disclaimer.

---

### Step 6 Database Model (`AssessmentReport`)

Table: `assessment_reports`  
Migration: `migrations/versions/fddebcfeb1c5_add_step_6_assessment_reports_table.py`

| Column | Type | Description |
|---|---|---|
| `id` | String(36) UUID | Primary key |
| `assessment_id` | FK → HealthAssessment | Parent assessment (`CASCADE`), indexed |
| `report_version` | Integer | Incremental snapshot version (`1, 2, 3...`) |
| `report_status` | String(30) | `GENERATED`, `UPDATED`, `ARCHIVED` |
| `generated_at` | DateTime(tz) | Point-in-time timestamp of report creation |
| `generated_by` | String(36) UUID | User ID who requested generation |
| `report_data` | JSON | Complete 13-section immutable structured clinical snapshot |
| `disclaimer` | Text | Mandatory veterinary safety disclaimer |
| `created_at` | DateTime(tz) | Audit creation timestamp |
| `updated_at` | DateTime(tz) | Audit update timestamp |
| **Unique** | `(assessment_id, report_version)` | Guarantees version integrity per assessment |

---

### Step 6 APIs

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/assessments/<id>/reports` | JWT | Generate a new immutable report snapshot (returns `201 Created`) |
| `GET` | `/api/v1/assessments/<id>/reports` | JWT | List historical report snapshots for assessment (ordered `v_latest` to `v1`) |
| `GET` | `/api/v1/reports/<id>` | JWT | Retrieve complete structured report by ID (JSON) |
| `GET` | `/api/v1/reports/<id>/html` | JWT | Render standalone, styled, injection-safe HTML report for viewing or print |

*Content Negotiation:* Calling `GET /api/v1/reports/<id>` with header `Accept: text/html` automatically serves the rendered HTML document.

---

### Mandatory Clinical Safety Notice

> **VetVision AI provides AI-assisted health risk and early-warning information for informational and triage support.**
> It does **NOT** provide a definitive veterinary diagnosis and does not replace examination or advice from a qualified veterinarian.
> Seek professional veterinary care when symptoms are concerning, worsening, or urgent.
> The system strictly avoids prescribing medication, inventing clinical history, fabricating ML confidence metrics, or altering emergency triage priorities.

---

## 15. Running Tests & Code Coverage

```bash
cd backend

# Run all test suites (Steps 1 through 6)
.\venv\Scripts\pytest -v

# Run with test coverage analysis
.\venv\Scripts\pytest -v --cov=app tests/
```

**Test Suite Verification Results (Step 8B Complete):**
- **153 / 154 tests passing** (1 skipped — text question test)
- **92% Code Coverage** across 3,200+ statements
- **0 regressions** — all previous tests from Steps 1–8A pass completely.

---

## 16. Step 8A — Evidence Normalization, Risk-Scoring Reliability & Explainability

### Overview

Step 8A strengthens the clinical intelligence foundation of VetVision AI without inventing artificial machine-learning claims or altering the safety envelope. It introduces:
1. **Typed Evidence Representation**:
   - `NormalizedEvidence`, `EvidenceItem`, `EvidenceSource` (`symptom`, `observation`, `follow_up`, `image`, `pet_profile`).
   - `EvidenceStatus`: `PRESENT`, `ABSENT`, `UNKNOWN`, `CONTRADICTORY`.
   - **Missing Data Safety**: Fields that are unobserved, questions left unanswered, and photos not uploaded or not analyzed are strictly classified as `UNKNOWN` and added to `unknown_evidence_fields`. They are never treated as negative or reassuring evidence.
2. **Robust Type Handling**:
   - Explicit boolean, string, and null conversion for observations (specifically `pain_observed`, which safely maps `"true"`, `True`, `"none"`, `"severe"`).
3. **Data Quality & Contradiction Checker (`QualityChecker`)**:
   - Flags conflicting respiratory signs (e.g., normal breathing observed despite severe respiratory symptom).
   - Flags conflicting activity levels (e.g., normal activity recorded alongside severe lethargy/collapse).
   - Chronological anomaly detection (e.g., reported symptom duration exceeding the pet's calculated age).
   - Image quality gating: flags poor-quality or unanalyzed photos as data quality warnings without treating unanalyzed images as normal.
4. **Structured Factor Explainability (`StructuredFactor`)**:
   - Replaces vague explanation lists with structured attribution objects: `name`, `finding`, `source`, `status`, `direction` (`risk-increasing`, `reassuring`, `unknown`, `emergency override`), `rule_applied`, `rationale`, and `contribution_pts`.
5. **Score Clamping & Emergency Hard-Stop Inviolability**:
   - Sub-score contributions are mathematically bounded; the final score is strictly clamped to $[0, 100]$.
   - Authoritative emergency hard-stop enforces a 90-point floor and emergency triage status whenever acute clinical flags are active.
6. **Report Immutability**:
   - Structured factors and data quality warnings are stored directly within the existing `factor_breakdown` JSON column without requiring destructive schema migrations.

---

## 17. Step 8B — Enhanced Computer Vision & Image Analysis Reliability

### Overview

Step 8B improves photographic evidence quality assessment, actionable guidance, and duplicate evidence handling:
1. **Deterministic Computer Vision Quality Gate**:
   - **Blur / Edge Sharpness**: Calculated via edge filtering energy (`FIND_EDGES`). Images with low edge variance and low peak edge transitions are flagged for excessive blur/camera instability.
   - **Luminance / Brightness**: Evaluates mean grayscale illumination. Images below $35.0$ (severe underexposure) or above $240.0$ (overexposure/glare) are gated.
   - **Contrast**: Evaluates standard deviation of grayscale pixels. Images below $12.0$ (flat/washed out) are gated.
   - **Resolution & Aspect Ratio**: Enforces minimum dimensions ($150\times 150\text{ px}$) and maximum aspect ratio distortion ($[0.2, 5.0]$).
2. **Actionable User Guidance**:
   - Rather than opaque errors, owners receive targeted corrective actions: *"Ensure the room or pet is well lit..."*, *"Hold the camera steady or tap to focus..."*, *"Move closer to the area of concern..."*, *"Avoid harsh camera flash or direct glare..."*.
3. **Objective Visual Features vs. Non-Diagnostic Guardrails**:
   - Detects measurable color features (erythema chromatic ratio) and tags them with non-diagnostic labels (`"Localized Erythema Feature (Early Visual Marker, Not Disease Diagnosis)"`).
4. **Duplicate Evidence Prevention**:
   - Multiple photos of the same issue are not scored repeatedly (first photo contributes, duplicates assign $0\text{ pts}$ with explainability notes).
   - If owner already reported a corresponding skin symptom, photographic erythema is treated as corroborating evidence (modulated $+2\text{ pts}$ instead of $+5\text{ pts}$).
5. **Emergency Inviolability**:
   - Reassuring photographs cannot downgrade an emergency triage condition.

---

## 18. Implementation Roadmap

| Step | Description | Status |
|---|---|---|
| **Step 1** | Backend Foundation — Auth, Users, Pets, DB, JWT, Migrations | ✅ Complete |
| **Step 2** | Pet Health Assessment — Symptoms, Observations, Notes, AI Data Prep | ✅ Complete |
| **Step 3** | Dynamic Question Engine — Follow-Up Q&A, Emergency Triage, Conditional Logic | ✅ Complete |
| **Step 4** | AI Health Risk Analysis Engine — Explainable Scoring, Emergency Hard-Stop, ML Adapter | ✅ Complete |
| **Step 5** | Image Analysis Pipeline — Computer Vision Quality Gate, Observations & ML Adapter | ✅ Complete |
| **Step 6** | Veterinary Report & Explainable Health Summary — Versioning, 13 Sections, HTML Render | ✅ Complete |
| **Step 7** | Frontend Integration & UI — Web-based Assessment Workflow & Report Viewer | ✅ Complete |
| **Step 8A** | Intelligence & Explainability Upgrade — Evidence Normalization, Contradictions, Clamped Attribution | ✅ Complete |
| **Step 8B** | Enhanced CV & Image Reliability — Quality Metrics, Guidance, Duplicate Prevention | ✅ Complete |





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

# Run all 43 tests
.\venv\Scripts\pytest -v

# Run with coverage report
.\venv\Scripts\pytest --cov=app tests/
```

**Results:**
- **43 / 43 tests passing** (100%)
- **92% Total Code Coverage** across all models, services, schemas, and routes.

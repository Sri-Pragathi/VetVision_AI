# VetVision AI 🐾
### AI-Powered Pet Health Early Warning & Veterinary Assistance System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask 3.0](https://img.shields.io/badge/flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style](https://img.shields.io/badge/code%20style-PEP8-black.svg)](https://peps.python.org/pep-0008/)
[![Tests](https://img.shields.io/badge/tests-43%20passed%20(100%25)-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)]()

---

## 📌 Executive Summary

**VetVision AI** is an intelligent veterinary assistance system engineered for university-level innovation and technology competitions. The platform aids pet owners and veterinarians by detecting early warning signs of disease, identifying emergency conditions, tracking longitudinal pet health, and generating structured clinical summaries.

---

## 🏗️ Repository Structure

```text
VetVision_AI/
├── backend/                 # Modular Flask REST API backend
│   ├── app/                 # Application package (models, routes, schemas, services)
│   ├── migrations/          # Alembic database migrations
│   ├── tests/               # Pytest automated test suite (43 passed, 92% coverage)
│   ├── .env.example         # Environment template
│   ├── requirements.txt     # Backend dependencies
│   ├── run.py               # WSGI Entrypoint & symptom seeder
│   └── README.md            # Comprehensive technical guide
└── README.md                # Project root documentation
```

---

## 🚀 Implemented Capabilities (Step 1 & Step 2)

### Step 1: Core Foundation & Multi-Tenant Architecture
- **Authentication**: JWT access & refresh tokens with database-backed token blocklist for immediate revocation on logout.
- **Pet Management**: Full multi-tenant CRUD with owner isolation (zero cross-user inspection, modification, or deletion).
- **Security**: Bcrypt password hashing (12 rounds), centralized error sanitization (no leaked traces/secrets).
- **Database**: PostgreSQL support via environment variables with zero-config SQLite fallback.

### Step 2: Structured Pet Health Assessment & Triage
- **Clinical Symptom Vocabulary**: 20 seeded clinical categories (vomiting, difficulty breathing, seizures, itching, etc.) with category filtering.
- **Health Assessment Lifecycle**: Strict state-machine transitions (`in_progress` → `completed` or `cancelled`).
- **Clinical Associations**: Attach multiple symptoms with validated severity (`mild`, `moderate`, `severe`) and positive durations.
- **Physiological Observations**: Structured metrics (appetite, water intake, activity, breathing, pain, sleep, stool, urine).
- **Assessment Notes**: Free-text clinical and owner observations.
- **AI-Ready Transformation Engine**: `AiDataPreparationService` converts assessment sessions into a normalized JSON payload for future AI inference.
- **Emergency Screening Interface**: `EmergencyAssessmentService` identifies urgent clinical warning flags and provides safety disclaimers.

For full endpoint specifications, diagrams, and payloads, see [backend/README.md](file:///c:/Users/gsrip/OneDrive/Desktop/VetVision%20AI/backend/README.md).

---

## 🧪 Testing & Quality Assurance

```bash
cd backend
.\venv\Scripts\pytest -v --cov=app tests/
```

- **43 tests executed — 43 passed (100% pass rate)**
- **92% code coverage** across all modules
- Zero warnings, zero errors

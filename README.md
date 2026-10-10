# VetVision AI 🐾
### AI-Powered Pet Health Early Warning & Veterinary Assistance Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask 3.0](https://img.shields.io/badge/flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![React 19](https://img.shields.io/badge/react-19-blue.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/vite-6-purple.svg)](https://vite.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Backend Tests](https://img.shields.io/badge/backend%20tests-140%20passed%20(100%25)-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)]()

---

## 📌 Executive Summary

**VetVision AI** is an intelligent veterinary-assistive health technology platform engineered for hackathons, innovation competitions, and production-grade deployments. The system assists pet parents and veterinary clinicians by facilitating guided health assessments, adaptive clinical inquiry, computer-vision image quality screening, transparent risk triage, and exportable veterinary handoff summaries.

> **Medical Caution & Clinical Disclaimer**: VetVision AI is strictly an early-warning triage and decision-support assistant. It does **not** provide definitive diagnoses and does not replace in-person veterinary examination. Critical indicators trigger automated emergency hard-stops.

---

## 🏗️ Repository Architecture

```text
VetVision_AI/
├── backend/                 # Modular Flask REST API backend
│   ├── app/                 # Core architecture (models, routes, schemas, services)
│   ├── migrations/          # Alembic database migrations
│   ├── tests/               # Pytest automated test suite (130 passed, 92% coverage)
│   ├── .env.example         # Environment template
│   ├── requirements.txt     # Python backend dependencies
│   ├── run.py               # WSGI Entrypoint & symptom/question seeders
│   └── README.md            # Comprehensive backend documentation
├── frontend/                # Healthcare-Grade React SPA
│   ├── src/
│   │   ├── api/             # Centralized API service layer (auth, pets, triage, reports)
│   │   ├── components/      # Common UI components (Navbar, Footer, TriageBadge, etc.)
│   │   ├── context/         # AuthContext & JWT session management
│   │   ├── pages/           # Clinical pages (Dashboard, Wizard, Reports, Pet Profiles)
│   │   ├── App.jsx          # Route configuration & ProtectedRoute wrappers
│   │   └── index.css        # Vanilla CSS Design System & Theme Tokens
│   ├── package.json         # React 19, Vite, Lucide-react, Axios
│   └── vite.config.js       # Vite bundler configuration & backend API proxy
└── README.md                # Project master documentation
```

---

## 🚀 Complete Development Roadmap (Steps 1–7)

### ✅ Step 1 — Backend Foundation & Multi-Tenant Authentication
- JWT access and refresh token authentication with token revocation blocklist.
- Full pet profile management isolated strictly to authenticated owners.
- Production-grade error handling, schema validation, and SQLite / PostgreSQL switching.

### ✅ Step 2 — Pet Health Assessment Backend
- Controlled clinical symptom catalog with 20+ veterinary symptom classifications.
- Structured physiological observations (appetite, water intake, respiration, pain).
- `AiDataPreparationService` and `EmergencyAssessmentService`.

### ✅ Step 3 — Dynamic Symptom & Follow-Up Question Engine
- Adaptive clinical question bank prioritizing high-acuity concerns based on symptoms.
- Dynamic question delivery (`GET /assessments/<id>/next-questions`).
- Answers state engine tracking clinical risk indicators and emergency answers.

### ✅ Step 4 — AI Health Risk Analysis Engine
- Pluggable scoring architecture: `BaseRiskAnalysisEngine` + `RuleBasedRiskAnalysisEngine`.
- Transparent 0–100 risk score with explicit contributing factor weights.
- Unbreakable **Emergency Hard-Stop Rule**: acute signs automatically lock risk score $\ge 90$ and trigger immediate hospital redirection.

### ✅ Step 5 — Computer Vision / Pet Image Analysis Pipeline
- Multipart photographic upload for affected areas, lesions, and eyes.
- Computer Vision Quality Gate evaluating resolution, lighting, sharpness, and color variance.
- Visual observations and feature tagging feeding into the overall risk assessment.

### ✅ Step 6 — Veterinary Report & Explainable Health Summary
- Versioned, immutable snapshot generation (`AssessmentReport`).
- Complete 13-section report structure with plain-text **Veterinary Handoff Summary**.
- Print-ready and standalone HTML report rendering (`GET /reports/<id>/html`).

### ✅ Step 7 — Professional React Frontend (Vite + Vanilla CSS)
- **Hospital-Grade UI Design**: Custom design system tokens, accessible typography, glassmorphism accents, and color-coded triage indicators.
- **7-Step Guided Assessment Wizard**:
  1. Patient Demographics & Profile Selection
  2. Multi-Category Symptom Picker with Severity & Chronicity Selectors
  3. Dynamic Adaptive Follow-up Question Prompts
  4. Clinical Observations Matrix (appetite, respiration, pain check)
  5. Photographic Upload with Computer Vision Quality Gate evaluation
  6. Review & Verification
  7. AI Health Risk Dial, Explainability Attribution, and Immediate Emergency Alerts
- **One-Click Clinical Handoff Copy**: Formatted plain-text summary designed to be copied directly into clinic registration emails or portals.
- **Comprehensive Management**: Dashboard metrics, Pet Profile Manager with edit/delete modals, and Reports Archive.

### ✅ Step 8A — Evidence Normalization, Risk-Scoring Reliability & Explainability Upgrade
- **Typed Evidence Modeling**: `NormalizedEvidence`, `EvidenceItem`, `EvidenceSource`, and explicit `EvidenceStatus` (`PRESENT`, `ABSENT`, `UNKNOWN`, `CONTRADICTORY`).
- **Missing Data Safety**: Unobserved metrics, unanswered follow-ups, and unanalyzed photos strictly remain `UNKNOWN` and never imply healthy/reassuring findings.
- **Robust Type Handling**: Safe parsers handle booleans, strings, and null observation values (`pain_observed`).
- **Data Quality & Contradiction Detection**: `QualityChecker` flags conflicting clinical observations, chronicity anomalies (e.g., symptom duration exceeding pet age), and poor/missing photo quality gates.
- **Granular Explainability Attribution**: `StructuredFactor` models provide exact source attribution, clinical direction (`risk-increasing`, `reassuring`, `unknown`, `emergency override`), applied rules, and verified contribution points.
- **Emergency Hard-Stop Integrity**: Authoritative floor of 90 points and immediate triage emergency hard-stop cannot be downgraded or discounted by secondary findings.
### ✅ Step 8B — Enhanced Computer Vision & Image Analysis Reliability
- **Deterministic Quality Metrics**: High-accuracy deterministic computer-vision checks for edge sharpness/blur (`edge_energy`, `edge_max`), luminance/brightness (`[35.0, 240.0]`), contrast (`MIN_CONTRAST = 12.0`), resolution (`MIN_DIMENSION = 150px`), and aspect ratio distortion (`[0.2, 5.0]`).
- **Actionable Quality Feedback**: Real-time user guidance on camera stability, ambient room lighting, capture distance, and lens angle for any rejected photo.
- **Measurable Visual Observations vs. Diagnostic Limitations**: Clearly documents detectable chromatic/color distribution features (e.g., localized erythema chromatic shift) with explicit disclaimers that basic image processing cannot diagnose clinical diseases.
- **Duplicate Evidence Prevention**: Prevents double-counting when owners upload multiple photos of the same lesion or when photographic erythema corroborates an already-reported skin symptom (modulated +2 pts instead of uncoupled +5 pts).
- **Missing/Failed Photo Safety**: Unanalyzed or rejected photos are recorded as `UNKNOWN` with zero risk points and never imply a clean bill of health.
- **Emergency Floor Inviolability**: A visually normal photograph can never cancel, discount, or delay care for critical clinical symptoms.

### ✅ Step 8C — End-to-End Validation, Security Hardening & Innovation Day Demo Readiness
- **Complete 16-Step User Journey Integration Suite**: Automated integration testing verifying the full user lifecycle from registration, pet profile creation, symptom intake, dynamic follow-up Q&A, and clinical observations, through photographic quality gate evaluation, risk scoring, versioned report generation, print-friendly rendering, and JWT logout/revocation.
- **Runtime Question Bank Seeding**: Ensured all 200+ clinical follow-up questions and standard symptoms are automatically seeded on runtime startup (`python run.py`), guaranteeing an out-of-the-box working experience on fresh SQLite or PostgreSQL setups.
- **Safe Development Demo Account Initializer**: Automatically provisions a clean local evaluation account (`john.doe@vetvision.ai` / `Password123!`) with sample pet `Max` on development boot, while enforcing that development demo helpers cannot bypass authentication or run in production.
- **Production Secret Guard**: Hardened application factory to refuse booting in `production` mode if insecure fallback or placeholder secrets are detected in `.env`.
- **Negative & Edge-Case Protection**: Verified multi-tenant isolation (403), cancelled assessment lifecycle locks, HTML XSS escaping, emergency override inviolability with reassuring photos, and immutable archived report snapshots.

---

## ⚡ Quick Start Guide

### 1. Start the Flask Backend

```bash
# Navigate to backend
cd backend

# Create & activate virtual environment (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run database migrations & seed symptoms/questions
flask db upgrade
python run.py
```
*Backend runs on `http://127.0.0.1:5000`.*

### 2. Start the React Frontend

```bash
# Open a new terminal in the frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
*Frontend runs on `http://localhost:3000` (proxies `/api` requests to Flask on port 5000).*

### 3. Quick Demo Credentials (Pre-Seeded for Local Development)
- **Email**: `john.doe@vetvision.ai`
- **Password**: `Password123!` *(or configured via optional `DEV_DEMO_PASSWORD` in `.env`)*
*(Or click the **"Quick-Fill Innovation Day Demo Credentials"** button on the Login page).*

---

## 🧪 Automated Testing & Verification

Run the comprehensive Pytest backend suite (all 158 tests pass):

```bash
cd backend
pytest -v
```

Build the production frontend bundle:

```bash
cd frontend
npm run build
```

---

## ⚖️ Clinical Safety & Ethics Statement

VetVision AI was engineered from the ground up with clinical safety constraints:
1. **No Hallucinated Diagnoses**: The system never declares definitive diagnoses. It acts as a triage and risk-scoring aid.
2. **Deterministic Emergency Overrides**: Critical symptoms (e.g., severe dyspnea, cyanosis, seizures, acute trauma) immediately enforce high triage urgency regardless of secondary factors.
3. **Transparent Explainability**: Every point of risk is mapped to an observable finding (duration, co-occurring symptoms, physical observations, image quality).

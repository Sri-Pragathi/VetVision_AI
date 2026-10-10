# VetVision AI — Step 9A: Final Deployment Readiness Audit Report

> **AUDIT SNAPSHOT NOTICE**
> **Status:** AUDIT SNAPSHOT ONLY (Recorded at commit `df982df`).
> **Important:** This document is a formal record of findings, architectural gaps, and deployment risks identified during the Step 9A audit. **It does NOT represent proof that these deployment issues have been resolved.** The findings documented here serve as the approved backlog and prerequisite specification for implementation in Step 9B.

---

## 1. Executive Summary & Audit Baseline

An empirical, read-only deployment readiness audit of VetVision AI was conducted at commit `df982df` on the `main` branch. The system's current implementation was evaluated against production deployment standards across cloud container hosting, multi-worker WSGI runtime, managed databases, cross-origin web routing, and persistent storage.

### Verified Baseline Facts

| Inspection Area | Baseline Status | Verification Evidence |
|---|:---:|---|
| **Git Repository State** | Clean Working Tree | Branch `main` at `df982df`; synchronized with `origin/main`. |
| **Local Backend Startup** | Functional (Dev Only) | `python run.py` binds `0.0.0.0:5000` via Werkzeug server. |
| **Local Frontend Startup** | Functional (Dev Only) | `npm run dev` serves Vite on port `3000`, proxying `/api` to port `5000`. |
| **Documentation Alignment** | Verified for Local Dev | Ports 5000 and 3000 match actual local configs in `README.md`. |
| **Seeding Idempotency** | Verified | Fresh database seeds 20 symptoms and 47 questions; repeat run seeds 0 duplicates. |
| **Production Secret Guard** | Verified | Application factory throws `ValueError` when production mode is given default or empty secrets. |
| **Database Migrations** | Current at Head | Alembic revision `fddebcfeb1c5 (head)` with 6 completed migration scripts. |
| **Backend Test Suite** | 158 Passed, 1 Skipped | Comprehensive test coverage (93%) across 3,222 statements. |
| **Frontend Production Build** | Compiles Cleanly | `npm run build` succeeds in ~300ms without bundler errors. |

---

## 2. Four Critical Deployment Blockers (P1)

The following four defects represent **immediate showstoppers** that will prevent a functional deployment in standard production cloud environments (such as Render, Vercel, Railway, or Docker).

### Blocker 1: CORS Configuration Fails for Multiple Origins
- **Location:** `backend/app/__init__.py:L48-49` and `backend/.env.example:L21`
- **Issue:**
  `backend/.env.example` documents comma-separated origins:
  ```bash
  CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173
  ```
  However, `backend/app/__init__.py` passes this string literal directly into `Flask-Cors`:
  ```python
  cors_origins = application.config.get("CORS_ORIGINS", "*")
  cors.init_app(application, resources={r"/api/*": {"origins": cors_origins}})
  ```
- **Empirical Test Verification:**
  When passed as a comma-separated string, `Flask-Cors` performs an exact string equality check against the browser's `Origin` header.
  - Test with comma string: `Access-Control-Allow-Origin` present? **`False`** (Blocked by browser)
  - Test with parsed list (`[o.strip() for o in s.split(',') if o.strip()]`): `Access-Control-Allow-Origin` present? **`True`** (Allowed)
- **Production Impact:** Any split deployment (e.g., Frontend on Vercel, Backend on Render) setting multiple origins in `CORS_ORIGINS` will result in all API calls being blocked by browser CORS policy.

---

### Blocker 2: Production WSGI (Gunicorn) Never Seeds Clinical Data
- **Location:** `backend/run.py:L10-25` and `backend/migrations/versions/`
- **Issue:**
  Clinical vocabularies (`seed_symptoms()` and `seed_follow_up_questions()`) are exclusively invoked inside:
  ```python
  if __name__ == "__main__":
      with app.app_context():
          ...
          seed_symptoms()
          seed_follow_up_questions()
  ```
  When booted under production WSGI servers (e.g., `gunicorn run:app` or `gunicorn "app:create_app('production')"`), `__name__ == "__main__"` is `False`.
  Furthermore, the database migration scripts in `backend/migrations/versions/` only create empty tables and do not seed any clinical data.
- **Production Impact:** A fresh production deployment running standard commands (`flask db upgrade` followed by `gunicorn`) boots with an empty symptom bank and zero follow-up questions. Users cannot select symptoms or proceed through assessments.

---

### Blocker 3: Frontend SPA Deep-Linking & Page Reloads Return 404
- **Location:** `frontend/src/App.jsx:L2`
- **Issue:**
  The frontend uses React Router's HTML5 history API (`BrowserRouter`).
  When compiled to static assets (`npm run build`), there are no single-page application (SPA) rewrite rules configured (e.g., missing `_redirects` for Netlify/Render Static or `vercel.json` rewrite for Vercel).
- **Production Impact:** Direct navigation or refreshing any sub-route (such as `/dashboard`, `/pets`, `/assessments`, or `/reports/:id`) results in an HTTP 404 Not Found error served by the static hosting provider.

---

### Blocker 4: Missing Frontend Production API Base URL Configuration
- **Location:** `frontend/src/api/client.js:L4`
- **Issue:**
  `const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';`
  There is no `frontend/.env.example` in the codebase.
  Vite evaluates and bakes `import.meta.env` values into the client JavaScript bundle strictly at **build time** (`npm run build`).
- **Production Impact:** If a developer or automated CI builds the frontend without explicitly setting `VITE_API_BASE_URL=https://<backend-domain>/api/v1`, the bundle defaults to relative `/api/v1`. On separate-origin hosting (e.g., Vercel frontend + Render backend), all client requests fail with 404 because the static host attempts to resolve `/api/v1` locally.

---

## 3. Additional Security & Operational Risks

1. **Ephemeral Local Storage for Image Uploads:**
   - `backend/app/services/storage_service.py` saves uploaded pet images to `backend/uploads/` on the local disk.
   - On containerized platforms (Render, Railway, Heroku), local disk storage is **ephemeral**. Any container restart, redeploy, or dyno sleep wipes all uploaded files.
   - In multi-worker deployments (e.g., 2+ Gunicorn workers), an image uploaded through Worker A is not guaranteed to be accessible to Worker B during computer vision analysis.
2. **SQLite Database Limitations in Production:**
   - `DevelopmentConfig` defaults to SQLite (`vetvision_dev.db`). SQLite locks on concurrent write operations and cannot persist data across container restarts. Production deployments must enforce managed PostgreSQL.
3. **No Dedicated Database Seed CLI Command:**
   - There is no Flask CLI command (e.g., `flask seed-db`) to execute idempotent data seeding in automated deployment release steps.
4. **Development Server Execution in README:**
   - The root README currently instructs users to run `python run.py`, which boots Flask's built-in Werkzeug development server. It does not document WSGI entrypoints or worker flags for production.

---

## 4. Recommended Deployment Architecture (Production / Cloud Hosting)

To maintain a zero-cost tier while ensuring high reliability, uptime, and demonstration readiness:

```
┌──────────────────────────────────────┐          ┌──────────────────────────────────────┐
│       Frontend (Vercel / Netlify)    │          │        Backend (Render / Railway)    │
│  - Static SPA Build (frontend/dist)  │  HTTPS   │  - Gunicorn WSGI (2 workers)         │
│  - SPA Rewrite (/* -> /index.html)   ├─────────►│  - Flask App Factory (production)    │
│  - Build env: VITE_API_BASE_URL      │          │  - CORS: parsed list from env        │
└──────────────────────────────────────┘          └──────────────────┬───────────────────┘
                                                                     │
                                                  ┌──────────────────┴───────────────────┐
                                                  │       PostgreSQL Database            │
                                                  │  - Neon / Supabase / Render PG       │
                                                  │  - SSL mode: require                 │
                                                  └──────────────────────────────────────┘
```

- **Frontend Hosting:** Vercel or Render Static Site (Free Tier)
  - Build Command: `npm run build`
  - Output Directory: `dist`
  - SPA Rewrites: Configured via `vercel.json` or `_redirects`
  - Environment Variable: `VITE_API_BASE_URL=https://<backend-domain>/api/v1`
- **Backend Hosting:** Render Web Service (Free Tier)
  - Runtime: Python 3.11 / 3.12
  - Build Command: `pip install -r requirements.txt && flask db upgrade`
  - Start Command: `gunicorn -w 2 -b 0.0.0.0:$PORT run:app`
  - Pre-Deploy Release Command: `flask seed-db`
- **Database:** Managed Cloud PostgreSQL (Neon or Render PostgreSQL)
  - Connection string: `postgresql://user:pass@host/dbname?sslmode=require`

---

## 5. Prioritized Implementation Plan for Step 9B

| Priority | Component | Target Files | Implementation Action |
|:---:|---|---|---|
| **P1** | **Backend CORS Parsing** | `backend/app/__init__.py` | Split `CORS_ORIGINS` by commas into a clean list of allowed origin strings. |
| **P1** | **Production Seeding Command** | `backend/app/commands.py`, `backend/run.py` | Implement a `flask seed-db` CLI command; ensure `run:app` can seed data when invoked. |
| **P1** | **Frontend SPA Rewrites** | `frontend/public/_redirects`, `frontend/vercel.json` | Add rewrite rules so deep links (e.g., `/reports/123`) route to `index.html`. |
| **P2** | **Frontend Environment Documentation** | `frontend/.env.example` | Create sample environment configuration documenting `VITE_API_BASE_URL`. |
| **P2** | **Procfile & WSGI Entrypoint** | `backend/Procfile`, `Procfile` | Provide standard deployment Procfile (`web: gunicorn run:app`). |
| **P2** | **Production Setup Documentation** | `README.md`, `backend/README.md` | Document production environment variables, Gunicorn startup, and database setup. |
| **P3** | **Health Check Database Probe** | `backend/app/routes/health_routes.py` | Add database connectivity status to `/api/v1/health` for cloud liveness probes. |

---

*End of Step 9A Deployment Readiness Audit Record.*

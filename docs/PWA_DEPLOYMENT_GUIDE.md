# VetVision AI — Progressive Web App (PWA) Deployment & Production Guide

This document outlines the architecture, security policies, hosting setup, and environment configurations for deploying the VetVision AI Progressive Web App to production.

---

## 1. PWA Architectural Overview

VetVision AI is configured as a fully installable, standalone Progressive Web App (PWA).

### Key Components:
- **Web App Manifest:** [`frontend/public/manifest.webmanifest`](file:///c:/Users/gsrip/OneDrive/Desktop/VetVision%20AI/frontend/public/manifest.webmanifest)
  - Application Name: **VetVision AI**
  - Display Mode: **standalone**
  - Theme Color: `#0d9488` (Clinical Teal)
  - Background Color: `#f8fafc` (Slate)
  - Icons: `192x192`, `512x512`, and `maskable-512x512` adaptive icon.
- **Service Worker:** [`frontend/public/sw.js`](file:///c:/Users/gsrip/OneDrive/Desktop/VetVision%20AI/frontend/public/sw.js)
  - Pre-caches core application shell (`/index.html`, manifest, icons).
  - Uses Stale-While-Revalidate for content-hashed Vite static assets (`/assets/*.js`, `/assets/*.css`).
  - Network-first navigation fallback for offline app shell booting.
- **PWA Status & Offline Banner:** [`frontend/src/components/common/PwaStatusBanner.jsx`](file:///c:/Users/gsrip/OneDrive/Desktop/VetVision%20AI/frontend/src/components/common/PwaStatusBanner.jsx)
  - Notifies owners when offline with a clear explanation that clinical operations require a connection.
  - Automatically notifies owners when an application update is ready and offers a one-click reload.

---

## 2. Security & Clinical Data Protection Rules

VetVision AI handles private medical records, owner accounts, pet histories, and sensitive triage assessments. The Service Worker enforces strict security policies:

1. **Network-Only for All API Requests:**
   - Any request matching `/api/` or non-`GET` HTTP methods **bypasses Cache Storage completely**.
   - Private patient details, assessment answers, triage calculations, AI guidance replies, and doctor reviews are **never** stored in public browser caches.
2. **Zero Authentication Token Caching:**
   - Authorization headers and login responses are never intercepted or cached by the Service Worker.
3. **No Stale Medical Guidance:**
   - The app will never serve outdated clinical triage advice from an offline cache. If the user is offline during an assessment or AI consultation, the request fails safely and prompts the user to reconnect.

---

## 3. Production Deployment Configuration

### A. Frontend Deployment (Vercel, Netlify, Cloudflare Pages, or Render Static)

1. **HTTPS Enforcement:**
   - Service Workers **strictly require HTTPS** in production (browsers only allow HTTP on `localhost` during development). Ensure your custom domain has an active SSL/TLS certificate.
2. **Build Settings:**
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
3. **Build-Time Environment Variables:**
   - `VITE_API_BASE_URL`: The full URL to your deployed Flask backend API (e.g. `https://vetvision-api.onrender.com`).
   - If left blank, defaults to relative `/api/v1` (which requires a reverse proxy to your backend).

### B. Backend Deployment (Render, Railway, Fly.io, AWS, or Docker)

The backend provides the RESTful API and Groq AI inference. Ensure the following environment variables are set:

```ini
FLASK_ENV=production
FLASK_DEBUG=0

# Unique 32+ character secrets (app will refuse to start if default placeholders are used)
SECRET_KEY=generate-a-strong-random-secret-key-for-production
JWT_SECRET_KEY=generate-a-strong-random-jwt-secret-key-for-production

# Persistent PostgreSQL Database (Neon, Supabase, Render Postgres)
DATABASE_URL=postgresql://user:password@host:5432/vetvision_production?sslmode=require

# CORS Configuration (Must include your deployed frontend HTTPS URL)
CORS_ORIGINS=https://vetvision-app.vercel.app,https://vetvision.ai

# Groq LLM Inference API Key
GROQ_API_KEY=gsk_...
GROQ_MODEL=openai/gpt-oss-120b
```

---

## 4. Testing & Verification Checklist

| Test Item | Development Environment | Production HTTPS Environment |
|---|---|---|
| **Web App Manifest** | Served at `/manifest.webmanifest` (HTTP 200) | Validated in Chrome DevTools Application tab |
| **Service Worker Registration** | Registered via `sw.js` on `http://localhost:3000` | Registered under HTTPS domain |
| **PWA Installability** | Install icon in browser address bar (Chrome/Edge/Brave) | Install banner triggered on mobile Android & desktop |
| **Static Cache Isolation** | Shell cached; `/api/` network-only | Verified no sensitive medical responses in Cache Storage |
| **Offline Banner** | Triggers upon toggling Network Offline in DevTools | Triggers on device airplane mode |
| **Live API Operations** | Authenticated assessments, pet profiles, and AI chat functional | Authenticated assessments save to remote Postgres |

<div align="center">
  <h1>SmartDiner</h1>
  <p><b>An AI-powered restaurant assistant that mathematically guarantees allergen safety, budget compliance, and dietary adherence through a strict governed architecture.</b></p>

  <p>
    <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License MIT" />
    <img src="https://img.shields.io/badge/Next.js-15.0+-black.svg?logo=next.js" alt="Next.js" />
    <img src="https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi" alt="FastAPI" />
    <img src="https://img.shields.io/badge/PostgreSQL-16.0-336791.svg?logo=postgresql" alt="PostgreSQL" />
    <img src="https://img.shields.io/badge/PuLP-ILP_Solver-orange.svg" alt="PuLP" />
  </p>
  
  <p>
    <a href="https://github.com/ConsoleCzar-2/SmartDiner/wiki">Wiki & Documentation</a> · 
    <a href="https://github.com/ConsoleCzar-2/SmartDiner/wiki/API">API Reference</a>
  </p>
</div>

---

## Overview

SmartDiner acts as a fully autonomous concierge for restaurants. Unlike traditional LLM wrappers that hallucinate prices or forget fatal allergies, SmartDiner strictly separates natural language understanding from deterministic business logic. It uses a **multi-layered governed AI pipeline**:

1. **Intent Classification:** Identifies if the user is asking a question, making an order, modifying an order, or being adversarial. Questions are instantly routed to a lightweight Q&A LLM, bypassing heavy math.
2. **Context-Aware Extraction:** Parses natural language into strict JSON requirements using Gemini 3.5 Flash Lite, maintaining awareness of the user's ongoing draft cart.
3. **Multi-Venue Resolver:** Supports Restaurant-Agnostic Concierge mode directly from the landing page navbar. Finds, compares, and ranks dishes across multiple restaurants simultaneously.
4. **SQL Deterministic Filter:** Hard-filters the menu at the database level to ensure 100% allergen safety. Unsafe items never reach the AI.
5. **ILP Optimization Solver:** Uses Integer Linear Programming (PuLP) with course diversity bonuses, soft structure penalties, and anti-monopoly carb caps to mathematically guarantee budget and party nutrition.
6. **Grounded Explanation:** The LLM summarizes the mathematically-verified cart back to the user in a natural, hallucination-free response.
7. **Enriched WORM Audit Logging:** Asynchronously captures compiled SQL queries, cache hits, exact token counts, and solver bounds into immutable GCS Object-Locked blobs.
8. **Admin AI Business Intelligence:** Dual-source conversational BI engine in the admin dashboard synthesizing data from PostgreSQL analytics and GCS audit trails with strict RBAC.
9. **Dual-Tier In-Memory Caching:** Synchronized 300s TTL caching layer featuring **L1 Catalog Cache** (eliminating N+1 relational joins during whole-menu browsing) and **L2 Dynamic Filter Cache** (deterministic constraint-hashed memory cache for sub-millisecond AI chat refinements), governed by centralized system constants in `backend/app/constants.py`.

This multi-step governed architecture guarantees **100% safety and compliance** while maintaining conversational flexibility, live cart editing, and state persistence.

---

## Technical Stack

- **Frontend:** Next.js 14/15, React 18, TailwindCSS, Framer Motion, React Markdown (Glassmorphic UI)
- **Backend:** FastAPI, Python 3.12, SQLAlchemy 2.0 (Async), PuLP (Linear Programming)
- **Constants Layer:** `backend/app/constants.py` (Unified TTLs, platform currency, dining taxonomy)
- **Caching:** Dual-Tier in-memory cache (L1 Catalog + L2 Dynamic Constraint Filter)
- **Database:** PostgreSQL 16 (Strict constraints, JSONB state, UUIDv7 keys)
- **AI/LLM:** Google Gemini 3.5 Flash Lite (Structured Outputs)
- **Cloud/Infra:** Google Cloud Storage (GCS) for images & WORM compliance logging

---

## Installation & Setup

Both the backend and frontend must be run concurrently.

### 1. Start Infrastructure (Database)
Before running the backend, you must start the required infrastructure using Docker:
```bash
docker compose up -d db
```
*(This starts the PostgreSQL database on port 5433)*

### 2. Backend Setup
```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\activate 
# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Start the server (runs on http://localhost:8000)
uvicorn app.main:app --reload
```
*(The interactive Swagger UI for the API will be automatically generated and available at http://localhost:8000/docs)*

### 3. Frontend Setup
```bash
cd frontend
npm install
# Start the Next.js development server (runs on http://localhost:3000)
npm run dev
```

### 4. Database Seeding & Migration
To reset and populate the database with the 6 authentic restaurants (Spice Garden, Dragon's Wok, The Grand Kitchen, South Spice Heritage, Tokyo Umami, Green Haven Cafe) and 104 unique dishes:
```bash
cd backend

# Truncate tables cleanly
python -m seed.truncate_db

# Seed fresh data
python -m seed.seed_data

# (Optional) Seed remote Render production database:
python -m seed.seed_render --url="postgresql://<USER>:<PASSWORD>@<HOST>.render.com/<DB_NAME>" --yes
```

### 5. Google Cloud Credentials (Optional, for GCS features)

The `gcp-credentials.json` file in the repo root is **gitignored** and is only required if you want to exercise Google Cloud Storage features (image uploads, WORM audit-log retrieval). The backend (`backend/app/services/gcs_client.py`) automatically resolves credentials across environments:

- **Local Development:** Place the service-account JSON at `gcp-credentials.json` (repo root) or set `GOOGLE_APPLICATION_CREDENTIALS` in your `.env`.
- **Render Production:** Upload the file as a Render Secret File named `gcp-credentials.json` (automatically mounted and detected at `/etc/secrets/gcp-credentials.json`).
- **Raw Environment String:** Alternatively, set `GOOGLE_APPLICATION_CREDENTIALS_JSON` to the raw JSON string contents.

> **Do not commit this file as well as the other environment variables.** It is in `.gitignore` for a reason. If you accidentally leak a service-account key, rotate it immediately in the GCP console.

---

## Extensive Documentation

For deep technical dives into the engineering decisions, database schema, and LLM prompts, please consult our Wiki. All technical depth has been abstracted there to keep this readme clean:

- [Product Requirements Document (PRD)](https://github.com/ConsoleCzar-2/SmartDiner/wiki/PRD)
- [Architecture & Pipeline Design](https://github.com/ConsoleCzar-2/SmartDiner/wiki/ARCHITECTURE)
- [UML Diagrams (Class & Sequence)](https://github.com/ConsoleCzar-2/SmartDiner/wiki/UML)
- [Database & ERD](https://github.com/ConsoleCzar-2/SmartDiner/wiki/DATABASE)
- [REST API Reference](https://github.com/ConsoleCzar-2/SmartDiner/wiki/API)
- [Prompt Engineering & LLM Integration](https://github.com/ConsoleCzar-2/SmartDiner/wiki/PROMPTS)
- [Engineering Decision Log](https://github.com/ConsoleCzar-2/SmartDiner/wiki/DECISION_LOG)

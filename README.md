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

**SmartDiner** is an autonomous AI dining concierge that mathematically guarantees 100% allergen safety, budget compliance, and nutritional balance. Traditional LLM-based chatbots frequently hallucinate menu items, miscalculate prices, or overlook fatal allergens. SmartDiner solves this by strictly decoupling natural language interaction from deterministic business logic through a **four-layer governed pipeline**:

1. **Natural Language Understanding & Sequential Intent Gate:** Gemini 3.5 Flash Lite executes a fast intent gate (`ORDER`, `MODIFICATION`, `QUESTION`, `GREETING`, `OFF_TOPIC`, `ADVERSARIAL`), short-circuiting non-order inquiries directly to a lightweight read-only Q&A engine with lean cart projections. This bypasses the constraint extractor and ILP solver on question turns to cut token consumption by ~78%. Ordering and modification turns execute a gated constraint extractor with lean cart projections and compact sliding-window history.
2. **Deterministic SQL Filtering:** PostgreSQL and in-memory dual-tier caching (L1 Catalog + L2 Dynamic Filter) hard-filter candidate dishes at the database level via deep ingredient-to-allergen relations. Unsafe items never reach the AI.
3. **Mathematical ILP Optimization:** PuLP CBC Integer Linear Programming solver formulates a balanced meal plan under hard budget ceilings, headcount requirements, dietary allocations, course diversity bonuses, and anti-monopoly caps.
4. **Grounded Explanation & Compliance:** The verified cart is explained to the diner using grounded, hallucination-free prompts, while full session telemetry is asynchronously archived to Google Cloud Storage with WORM (Write Once, Read Many) Object-Lock compliance.

### Key Capabilities
- **Server-Sent Events (SSE) Streaming:** Real-time token streaming with instant cart dispatch (`event: cart`) as soon as the ILP solver finishes, eliminating response lag.
- **Global Concierge Mode:** Cross-restaurant search and package optimization across multiple culinary establishments directly from the landing page.
- **Dual-Source Admin AI Analytics:** Interactive executive dashboard with continuous zero-filled time series, cubic Bézier spline interpolation, and an AI intelligence concierge synthesizing PostgreSQL metrics and GCS audit trails.

---

## Technical Stack

- **Frontend:** Next.js 15 (App Router), React 19, TypeScript, TailwindCSS, Framer Motion, Lucide React, Server-Sent Events (SSE) streaming client.
- **Backend:** FastAPI, Python 3.12, Pydantic v2, SQLAlchemy 2.0 (Asyncpg), PuLP (CBC Mixed-Integer Linear Programming Solver), Google GenAI SDK (`google-genai`).
- **Data & Storage:** PostgreSQL 16 (strict constraints, UUIDv7 time-sorted keys, JSONB state persistence), Google Cloud Storage (GCS) with WORM Object-Lock compliance.
- **Architecture & Performance:** Dual-tier in-memory caching (L1 Catalog Cache + L2 Dynamic Constraint Cache), generator-first streaming core with unary REST adapters, centralized constants (`app.constants`), and centralized prompts module (`app.prompts`).

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
- [Testing](https://github.com/ConsoleCzar-2/SmartDiner/wiki/TEST_REPORT)
- [Engineering Decision Log](https://github.com/ConsoleCzar-2/SmartDiner/wiki/DECISION_LOG)


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

  <p><b>Team ConsoleCzar — Cimba.ai SDE Internship Take-Home</b></p>
  
  <p>
    <a href="https://github.com/ConsoleCzar-2/SmartDiner/wiki">Wiki & Documentation</a> · 
    <a href="https://github.com/ConsoleCzar-2/SmartDiner/wiki/API">API Reference</a>
  </p>
</div>

---

## Overview

SmartDiner acts as a fully autonomous concierge for restaurants. Unlike traditional LLM wrappers that hallucinate prices or forget fatal allergies, SmartDiner strictly separates natural language understanding from deterministic business logic. It uses a **multi-layered governed AI pipeline**:

1. **LLM Constraint Extraction:** Parses natural language ("5 people, 2 veg, under ₹3000") into strict JSON requirements using Gemini 3.5 Flash Lite.
2. **SQL Deterministic Filter:** Hard-filters the menu at the database level to ensure 100% allergen safety. Unsafe items (e.g. cross-contamination triggers) never reach the AI.
3. **ILP Optimization Solver:** Uses Integer Linear Programming (PuLP) to find the absolute mathematically optimal combination of dishes that satisfy the budget, dietary ratios, and party size.
4. **Grounded Explanation:** The LLM summarizes the mathematically-verified cart back to the user in a natural, hallucination-free response.

This dual-engine architecture guarantees **100% safety and compliance** while maintaining conversational flexibility.

---

## Technical Stack

- **Frontend:** Next.js 15, React, TailwindCSS, Framer Motion (Glassmorphic UI)
- **Backend:** FastAPI, Python 3.12, SQLAlchemy 2.0 (Async), PuLP (Linear Programming)
- **Database:** PostgreSQL 16 (Strict constraints, JSONB state, UUIDv7 keys)
- **AI/LLM:** Google Gemini 3.5 Flash Lite (Structured Outputs)
- **Cloud/Infra:** Google Cloud Storage (GCS) for images & WORM compliance logging

---

## Installation & Setup

Both the backend and frontend must be run concurrently.

### 1. Backend Setup
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

### 2. Frontend Setup
```bash
cd frontend
npm install
# Start the Next.js development server (runs on http://localhost:3000)
npm run dev
```

### 3. Database Seeding
To populate the database with sample restaurants, users, and rich menu items, run the data seeder:
```bash
cd backend
python -m seed.seed_data
```

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

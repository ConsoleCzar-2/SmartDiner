# SmartDiner Architecture


SmartDiner employs a "Governed AI Pipeline" architecture. Instead of relying on a single Large Language Model (LLM) to perform reasoning, math, and data retrieval simultaneously (which often leads to hallucinated prices, ignored allergies, and mathematical errors), SmartDiner strictly separates concerns.

## 1. High-Level System Architecture

```mermaid
flowchart TD
    Client[Next.js Client] -->|API Request| FastAPI[FastAPI Backend]
    FastAPI --> Pipeline[Governed Recommendation Pipeline]
    
    subgraph Pipeline [4-Step Governed Pipeline]
        direction TB
        Ext[1. LLM Constraint Extractor]
        DBF[2. PostgreSQL Menu Filter]
        ILP[3. PuLP Integer Linear Solver]
        Exp[4. LLM Explanation Generator]
        
        Ext -->|Extracted JSON| DBF
        DBF -->|Safe Candidate Items| ILP
        ILP -->|Mathematically Optimal Menu| Exp
    end
    
    Pipeline -.->|Response| FastAPI
    FastAPI -.->|JSON| Client
    
    %% Audit Logging Background Task
    FastAPI -.- |Background Task| WORM[(GCS WORM Bucket)]
    
    Ext <--> Gemini1[Gemini 3.5 Flash Lite]
    DBF <--> DB[(PostgreSQL 16)]
    Exp <--> Gemini2[Gemini 3.5 Flash Lite]
```

## 2. The 4-Step Governed Pipeline

### Step 1: Constraint Extraction (LLM)
The user's natural language input (e.g., "Food for 3, no nuts, budget ₹2000") is passed to Gemini 3.5 Flash Lite. The LLM is forced to return a strictly typed JSON object conforming to a Pydantic Schema.
- **Input:** Natural language + Conversation History + Previous State.
- **Output:** Structured JSON (`ExtractedConstraints`).
- **Safety:** Temperature is set to `0.1` to maximize determinism. Nullable properties ensure the LLM doesn't hallucinate default values when a constraint isn't mentioned.

### Step 2: Deterministic Menu Filtering (SQL)
The structured constraints are passed to the database layer. SQLAlchemy dynamically builds a query to fetch only the menu items that mathematically and factually satisfy the hard limits.
- **Action:** Filters out items exceeding `max_spice_level`, costing more than the entire `max_budget`, or containing any `excluded_allergens`.
- **Performance:** Employs an in-memory TTL caching layer to bypass heavy multi-table DB joins for frequently accessed menus, eliminating N+1 query latency.
- **Safety:** Allergens are traced deep into the relationship tree (`MenuItem -> Ingredient -> Allergen`), guaranteeing absolute dietary safety without relying on LLM reasoning.

### Step 3: ILP Optimization (PuLP Math Solver)
The filtered "safe" candidate items are passed to an Integer Linear Programming (ILP) solver. 
- **Objective:** Maximize `(Item Rating × Serving Size)` to provide the best value.
- **Constraints:** 
  - Total Cost ≤ `max_budget`
  - Total Servings ≥ `people_count`
  - Vegetarian Servings ≥ `vegetarian_count`
  - Vegan Servings ≥ `vegan_count`
  - Non-Veg Servings ≥ `non_vegetarian_count`
  - Total Servings ≤ `people_count * 4` (Reasonable Feast Limit)
- **Safety:** This step guarantees that the final menu perfectly respects the budget and feeding requirements. It eliminates the "bad math" problem inherent to autoregressive LLMs.

### Step 4: Explanation Generation (LLM)
The mathematically verified output from Step 3 is fed back into Gemini 3.5 Flash Lite alongside the original constraints.
- **Action:** Generates a friendly, 2-3 sentence summary explaining the recommendation.
- **Safety:** The system prompt strictly forbids hallucinating items, prices, or rationales outside of the injected solver context.

### Step 5: Compliance Audit Logging (Asynchronous)
Once the response is generated, a background task compiles the user's constraints, the math solver's output, and the LLM's explanation into a single structured JSON payload.
- **Action:** Uploads the payload to Google Cloud Storage (GCS).
- **Compliance:** The GCS bucket is configured with **Object Lock** to enforce WORM (Write Once, Read Many). This guarantees cryptographically that the AI's decision trail cannot be deleted or modified for the duration of the retention policy (e.g., 7 days or 1 year).

## 3. Technology Stack

### Frontend
- **Framework:** Next.js App Router with TypeScript
- **Styling:** Tailwind CSS + Framer Motion (glassmorphic UI, micro-animations)
- **State Management:** React Hooks and URL search parameters; API access uses `NEXT_PUBLIC_API_URL`.

### Backend
- **Framework:** FastAPI (Python 3.12+)
- **Database:** PostgreSQL 16 (via asyncpg)
- **ORM:** SQLAlchemy 2.0 + Alembic for migrations
- **AI/Math:** `google-genai` (Gemini API) + `PuLP` (CBC Solver)
- **Compliance Storage:** Google Cloud Storage (`google-cloud-storage`) with Object Lock (WORM).
- **Authentication:** JWT customer/admin login with role claims; password hashing uses Passlib with `bcrypt==4.0.1`.

### HTTP Surface
The backend provides a comprehensive REST API encompassing restaurant/menu browsing, AI-governed chat and state retrieval, customer registration, admin authentication, admin metrics, and full audit conversation listing. This API acts as the bridge between the React frontend and the governed pipeline.

## 4. Alternative Architectures Considered
- **Pure LLM Agent (e.g., LangChain/ReAct):** Initially considered using a ReAct loop where the LLM writes SQL queries. **Rejected** due to high latency, prompt injection vulnerabilities, and mathematical unreliability when summing up budgets.
- **Vector Database (RAG):** Considered for menu searching. **Rejected** because relational SQL filtering is overwhelmingly superior for exact-match exclusion (like deadly allergies) and numerical bounds (budget thresholds). Semantic search provides no value for strict dietary adherence.

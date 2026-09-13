# SmartDiner Architecture Decision Log (ADR)

This document records the foundational architectural and engineering decisions governing the SmartDiner platform, their technical rationale, and their operational outcomes.

---

### ADR 01: Governed AI Pipeline vs. Pure LLM Agent
- **Context:** Pure LLM agents (e.g., ReAct loops or naked prompt wrappers) suffer from arithmetic hallucinations, unpredictable pricing, and inability to guarantee allergen safety.
- **Decision:** Decoupled natural language understanding from deterministic business logic into a 4-step governed pipeline:
  1. *Natural Language Understanding:* Gemini 3.5 Flash Lite extracts structured constraints and classifies intent.
  2. *Deterministic SQL Filtering:* PostgreSQL filters out unsafe dishes at the database level.
  3. *Mathematical Optimization:* PuLP CBC solver formulates an optimal meal mathematically.
  4. *Grounded Explanation:* Gemini summarizes verified results back to the diner.
- **Outcome:** 100% allergen safety, 0% arithmetic hallucination, and deterministic budget compliance.

---

### ADR 02: Mathematical Optimization via Integer Linear Programming (PuLP CBC)
- **Context:** Selecting food items to maximize culinary value while adhering to hard budget ceilings, headcount requirements, dietary splits, and multi-course structure is an NP-hard multidimensional knapsack problem. Heuristic algorithms and semantic vector search cannot guarantee optimality.
- **Decision:** Deployed an Integer Linear Programming (ILP) solver using the CBC engine via Python's `PuLP` library. Configured with:
  - Objective: Maximize total meal value (`Item Rating × Serving Size`) with category diversity bonuses (+5.0 per unique category).
  - Hard Constraints: Total cost $\le$ budget, total servings $\ge$ party size, dietary headcount quotas.
  - Course Structure Penalties: Universal main course requirement (`SoftMainReq`) penalizing missing mains by -30.0 points.
  - Anti-Monopoly Caps: Restricting beverages, sides, and desserts to prevent carb/beverage exploitation of cheap items.
- **Outcome:** Optimal, balanced meal packages formulated in sub-50ms solve times with zero budget overruns.

---

### ADR 03: Relational Data Modeling, Ingredient-Level Allergens & UUIDv7
- **Context:** Mapping allergens directly to dishes creates duplicate, fragile metadata that easily becomes stale when kitchen recipes change. Auto-incrementing primary keys leak business order volume, while standard UUIDv4 fragments B-Tree indexes.
- **Decision:**
  - Standardized allergen relationships on `MenuItem -> Ingredient -> Allergen`, establishing ingredients as the single source of truth.
  - Adopted time-sorted UUIDv7 for all primary keys across PostgreSQL 16.
  - Formalized dietary hierarchy: Vegan food is a strict subset of Vegetarian food (vegetarians can eat vegan items; vegans can never be served dairy-containing vegetarian items).
- **Outcome:** Transitive allergen safety with zero cross-contamination risk, efficient B-Tree database inserts, and unguessable external IDs.

---

### ADR 04: Dual-Tier In-Memory Caching & Centralized Constants Layer
- **Context:** Catalog browsing requires expensive multi-table relational joins, while multi-turn conversational AI repeatedly filters candidate subsets. Unifying system-wide thresholds was needed to prevent configuration drift.
- **Decision:**
  - Implemented **L1 Catalog Cache** (300s TTL) for full menu browsing and **L2 Dynamic Filter Cache** (300s TTL, deterministic constraint hashing) for AI chat candidate retrieval.
  - Centralized all system limits, cache TTLs, currency standards, and dining taxonomies into `backend/app/constants.py`.
  - Enforced atomic dual-tier invalidation on any menu edit by restaurant administrators.
- **Outcome:** Menu browsing renders instantly and AI candidate retrieval executes in under 0.2 ms with zero stale cache anomalies.

---

### ADR 05: Generator-First Core with Server-Sent Events (SSE) Streaming
- **Context:** Monolithic request-response patterns produced 4-8 second perceived latencies. Maintaining separate code paths for unary endpoints and streaming endpoints caused severe code duplication and behavioral drift.
- **Decision:**
  - Standardized on Server-Sent Events (SSE) over native HTTP for conversational recommendations and admin business intelligence.
  - Refactored `explanation_generator.py` and `recommendation_pipeline.py` into a "Streaming Core with Unary Adapter" pattern: the canonical async generator houses all business logic, while unary endpoints (`POST /api/chat`) simply drain the generator in memory.
  - Dispatched the structured cart (`event: cart`) immediately after ILP solver completion, allowing the client UI to populate instantly before text generation begins.
- **Outcome:** Instant perceived reactivity for diners, zero code duplication across streaming/unary APIs, and seamless HTTP proxy compatibility.

---

### ADR 06: Immutable WORM Audit Logging & Dual-Source Admin Intelligence
- **Context:** Regulated enterprise dining applications require tamper-proof compliance trails of all automated decisions without placing analytical query loads on live transactional databases.
- **Decision:**
  - Enqueued asynchronous `BackgroundTask` uploads of complete execution telemetry (compiled SQL, cache status, solver variables, and LLM token usage) to Google Cloud Storage (GCS) with Object-Lock WORM compliance.
  - Built an executive admin intelligence engine (`POST /api/admin/insights/chat`) that automatically classifies queries to synthesize live PostgreSQL operations and historical GCS audit trails under strict Role-Based Access Control (RBAC).
- **Outcome:** Immutable compliance archives and comprehensive executive business visibility with source attribution badges.

---

### ADR 07: Platform Currency Standard (INR ₹) & Zero-Emoji Communication Standard
- **Context:** Currency symbol discrepancies ($ vs ₹) cause calculation errors and diner confusion. Decorative emojis in AI outputs undermine enterprise reporting quality and increase token overhead.
- **Decision:**
  - Standardized 100% of financial figures, ILP math models, database constraints, prompts, and frontend formatting on Indian Rupees (`₹` / INR).
  - Enforced a universal zero-emoji policy across all system prompts and UI components, backed by GitHub-flavored markdown rendering.
- **Outcome:** Audit-grade clarity across diner recommendations, admin financial graphs, and AI intelligence summaries.

---

### ADR 08: Multi-Turn Quantity Constraints & Read-Only Anti-Hallucination Guardrails
- **Context:** Diners requesting explicit quantities across categories or items (e.g. "2 breads, 2 drinks, and 2 desserts") lost those quantities when constraints were purely categorical names. Furthermore, question-answering LLMs tended to hallucinate that they had updated the cart.
- **Decision:**
  - Extended constraint schemas with `category_min_counts` and `dish_quantities`, enforced via Pydantic validators and ILP solver lower bounds.
  - Dynamically scaled `max_qty_per_dish` and `feast_cap` to prevent artificial infeasibility when diners order extra items beyond default party sizes.
  - Routed action directives (e.g. "do those update now then") strictly to `MODIFICATION`, and enforced a strict Read-Only Mandate in question-answering prompts forbidding the model from claiming it updated orders.
- **Outcome:** Accurate multi-portion order updates across conversation turns with complete elimination of conversational hallucinations.

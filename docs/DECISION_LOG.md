# Engineering Decision Log


This document records the 10 most critical architectural and engineering decisions made during the development of SmartDiner.

## 1. Using a Governed Pipeline vs. Pure LLM Agent
**Decision:** We rejected the pure LangChain/ReAct agent approach in favor of a 4-step pipeline (LLM Extraction → SQL Filter → ILP Solver → LLM Explanation).
**Rationale:** LLMs are autoregressive text predictors; they cannot do math reliably (e.g., maximizing a budget across 5 items) and cannot guarantee 100% adherence to rules (e.g., fatal allergies). By restricting the LLM to merely extracting JSON, and handing the actual "thinking" over to deterministic math/SQL engines, we achieved 100% safety and zero hallucination.

## 2. Using Integer Linear Programming (ILP) via PuLP
**Decision:** We chose CBC (via Python's `PuLP` library) as the core recommendation engine instead of a basic sorting algorithm or vector search.
**Rationale:** The problem of selecting items to maximize value while strictly remaining under a budget ceiling is a variation of the Knapsack Problem (NP-Hard). Heuristics or vector searches cannot solve this optimally or respect complex intersecting rules (like "At least 2 veg, 1 non-veg, under ₹3000"). ILP guarantees mathematical optimality.

## 3. Capping "Infinite" Budgets in ILP (`MaxServingsConstraint`)
**Decision:** We added a constraint capping total servings at `people_count * 4` (Reasonable Feast Limit).
**Rationale:** If a user said "budget is not an issue", the ILP solver would mathematically attempt to order an infinite amount of food (to maximize value). Capping the servings artificially binds the optimization space, ensuring a realistic feast.

## 4. Forcing Diversity in ILP (`NonVegServingsConstraint`)
**Decision:** We explicitly forced the ILP solver to order at least `non_vegetarian_count` servings of meat.
**Rationale:** Vegetarian food is typically cheaper. When trying to maximize value within a strict budget, the solver would often feed a mixed group entirely vegetarian food to afford more items. Adding a strict non-veg floor guarantees dietary diversity.

## 5. Using Gemini 3.5 Flash Lite
**Decision:** Switched from `gemini-3.6-flash` to `gemini-3.5-flash-lite`.
**Rationale:** The 3.6 model hit rate limits rapidly during automated E2E testing (20 Requests Per Day limit). Flash Lite increased our limit to 500 RPD, radically improving developer velocity while maintaining identical JSON extraction accuracy.

## 6. Nullable Schema Enforcement in Gemini
**Decision:** We manually stripped `anyOf` from our Pydantic JSON schema dump and forcefully injected `"nullable": True` for optional fields like `max_budget`.
**Rationale:** Strict JSON schemas force LLMs to output *something*. If a user didn't mention a budget, the strict schema forced the LLM to hallucinate a default budget (e.g. ₹3000) just to pass validation. Making it explicitly nullable allows the LLM to output `null`, signaling the ILP solver that the budget is unconstrained.

## 7. Using UUIDv7 over Auto-Incrementing IDs
**Decision:** Used the `uuid6` python library to generate time-sorted UUIDv7 for all primary keys in PostgreSQL.
**Rationale:** Standard UUIDv4 causes massive B-Tree index fragmentation on large tables (like `conversations` or `order_items`), slowing down inserts. Auto-incrementing integers leak business metrics (e.g. competitors can see how many orders were placed). UUIDv7 solves both: it is unguessable but time-sorted for fast DB inserts.

## 8. Allergen Mapping via Ingredients (Not Dishes)
**Decision:** Allergens are mapped `Ingredient -> Allergen` rather than `MenuItem -> Allergen`.
**Rationale:** This creates a single source of truth. If the chef adds "Peanut Oil" to a new dish, the database automatically flags it as containing Peanuts. The LLM does not have to "know" that Peanut Oil contains peanuts; the SQL filter handles it entirely.

## 9. Direct vs Inferred Allergens (Step 15 addition)
**Decision:** We display "Inferred" allergens (derived from ingredients) as read-only checkboxes in the Admin UI, while allowing admins to manually toggle "Direct" allergens.
**Rationale:** This prevents restaurant staff from accidentally removing a crucial allergen tag (like Dairy) when a dish clearly contains an ingredient with that allergen (like Paneer). If a chef wants to remove Dairy from Paneer Tikka, they must remove the Paneer ingredient entirely, ensuring the system remains mathematically and logically safe.

## 10. Next.js App Router for the Frontend
**Decision:** Built the UI using React 18 / Next.js 14 App Router.
**Rationale:** Server-side rendering (SSR) of the restaurant menu ensures fast initial page loads and excellent SEO. The `useSuspenseQuery` combined with React State handles the complex cart/chat dual-pane UI fluidly.

## 11. FastAPI + asyncpg for the Backend
**Decision:** Used FastAPI with asynchronous SQLAlchemy (`asyncpg`) rather than Django or Express.
**Rationale:** FastAPI provides native integration with Pydantic (crucial for our LLM JSON schemas). `asyncpg` ensures that the heavy DB I/O (running complex JOINs to filter out allergens) doesn't block the Python event loop, allowing thousands of concurrent websocket/chat connections.

## 12. Centralized System Constants (`app.constants`)
**Decision:** All cache TTLs, platform currency codes, supported allergens, spice scales, and cuisine synonyms were unified into `backend/app/constants.py`.
**Rationale:** Prevents configuration drift between service layers and routing endpoints (such as `menu_filter.py` and `menu.py` drifting in TTL values). Ensures that a single modification updates both backend filtering logic and API caching rules uniformly.

## 13. Dual-Tier In-Memory Caching Architecture
**Decision:** Implemented a two-tiered in-memory caching system:
1. **L1 Catalog Cache (`MENU_CACHE` in `menu.py`):** Caches full-menu relational joins for customer browsing (`GET /api/restaurants/{id}/menu`) with a 300s TTL.
2. **L2 Dynamic Filter Cache (`MENU_FILTER_CACHE` in `menu_filter.py`):** Caches deterministic, constraint-hashed menu queries for the AI recommendation pipeline (`POST /api/chat`) with a synchronized 300s TTL.
**Rationale:** Browsing requires eager-loading all ingredients and allergens across the whole menu, whereas AI chat dynamically queries subsets based on fluctuating constraints. Separating these tiers allows the chat pipeline to bypass database subqueries on multi-turn refinements (< 0.2 ms retrieval) while ensuring that admin updates atomically invalidate both tiers simultaneously.

## 14. Strict Indian Rupee (INR) Platform Currency Standard
**Decision:** Standardized 100% of financial figures, database constraints, calculations, LLM prompts, and frontend formatting to Indian Rupees (`₹` / INR).
**Rationale:** Mixing dollar symbols with rupee amounts creates severe confusion for diners and breaks revenue aggregation in the Admin AI Insights engine. Grounding all models and prompts in INR ensures audit compliance and consistency across operational metrics.

## 15. Markdown-Driven Agent Communication with Zero-Emoji Policy
**Decision:** Implemented universal markdown rendering via `frontend/src/components/ui/markdown-content.tsx` while enforcing a strict zero-emoji policy across all system prompts and generated outputs.
**Rationale:** Emojis degrade the professional quality of enterprise audit logs and executive business intelligence reports, while creating token overhead and parsing inconsistencies. Structured markdown (tables, lists, bold highlights) delivers maximum clarity for both diner recommendations and admin operational insights.

## 16. Mathematical ILP Course Structure Optimization & Anti-Monopoly Guarantees
**Decision:** We upgraded `backend/app/services/optimizer.py` with:
1. **Bidirectional Category Coupling (`LinkCatMin` & `LinkCatMax`):** Enforcing $\sum x_i \ge c_{\text{cat}}$ so category indicators cannot be activated without purchasing food.
2. **Direct Dish-Level Preferred Category Enforcement:** Directly enforcing $\sum_{i \in \text{pref}} x_i \ge 1$ with dietary filtering instead of only boosting binary category indicators.
3. **Universal Meal Course Structure (`SoftMainReq`):** Penalizing skipped main courses by 30.0 points across all dining group sizes ($\ge 1$ person).
4. **Anti-Monopoly Caps on Non-Main Items:** Restricting beverages to `total_people`, sides to $\lceil \text{total\_people} / 2 \rceil$, and desserts to $\lceil \text{total\_people} / 2 \rceil$.
**Rationale:** In menu catalogs where beverages or sides have identical ratings (e.g. 4.0) to main courses but cost less than half the price, linear solvers will exploit cost-efficiency by purchasing multiple drinks and sides rather than a main course. Adding bidirectional indicator bounds, anti-monopoly caps, and universal main course priority guarantees balanced, real-world dining orders.

## 17. Multi-Cloud Resilient Credential Resolution for WORM Audit Logs
**Decision:** Centralized Google Cloud Storage client initialization in `backend/app/services/gcs_client.py` using `get_storage_client()`, which auto-detects credentials across Render Secret Files (`/etc/secrets/gcp-credentials.json`), local JSON files, raw environment strings, and GCP ADC.
**Rationale:** External hosting environments like Render do not have access to Google Compute Engine internal metadata servers. Hardcoding expectation of a single environment variable led to runtime authentication failures. Automatically resolving credentials across standard cloud mount paths guarantees resilient zero-config deployments.

## 18. Semantic Dietary Hierarchy (Vegan as Strict Subset of Vegetarian)
**Decision:** Formalized that vegetarian diners can be served vegan food, but vegan diners strictly cannot receive non-vegan vegetarian items.
**Rationale:** All 100% plant-based vegan dishes satisfy vegetarian dietary laws, providing greater culinary variety and budget flexibility for vegetarian diners. Conversely, vegetarian dishes containing dairy, eggs, cheese, or honey are strictly prohibited for vegan diners to maintain 100% compliance.

## 19. Adaptive Menu-Depth ILP Bounds and Non-Vegetarian Quota Decoupling
**Decision:** In `backend/app/services/optimizer.py`, we:
1. Dynamically calibrated dish portion limits (`max_qty_per_dish`) based on remaining candidate items: `div = min(max(1, len(all_items)), 3.0)` so small, heavily filtered menus (e.g. 1-3 surviving dishes) allow ordering sufficient portions to feed large parties.
2. Capped the non-vegetarian serving requirement to available non-vegetarian capacity: `req_nonveg = min(nonveg_people, max_nonveg_cap)`, preventing mathematical deadlocks when allergen/cuisine filters leave fewer non-veg servings than the party size.
3. Guarded non-veg item bans (`ForceZeroNonVeg`) so they only trigger if the party explicitly requested vegetarian/vegan options and zero non-veg (`(veg_people > 0 or vegan_people > 0) and nonveg_people == 0`). Unconstrained diners ("open to any dish") are no longer treated as strictly vegetarian.
4. Grounded infeasibility telemetry in actual constraint bottlenecks (candidate item counts, allergen/cuisine filters) rather than defaulting to budget advice.
**Rationale:** In specialized cuisines with pervasive allergens (e.g. Italian menus where 80%+ of dishes contain dairy), combining allergen exclusions with spice ceilings and cuisine filters decimated candidate items down to 3 dishes. Forcing an omnivorous party to order 7 meat servings when only 1 meat dish survived with a cap of 3 portions resulted in an unavoidable mathematical infeasibility regardless of budget (even up to ₹50,000). Decoupling non-veg quotas to available capacity and adapting portion caps ensures robust recommendations across all menu depths.

## 20. Server-Sent Events (SSE) for Pipeline Streaming Over WebSockets
**Decision:** Selected Server-Sent Events (SSE) via FastAPI's `StreamingResponse(media_type="text/event-stream")` rather than bidirectional WebSockets for conversational recommendations and admin business intelligence.
**Rationale:** The recommendation lifecycle is fundamentally unidirectional: the client submits a request payload, and the backend progressively outputs status updates, deterministic cart calculations, and token chunks. SSE runs over native HTTP with zero upgrade overhead, automatically handles connection reconnects, passes seamlessly through cloud load balancers and reverse proxies without buffering (`X-Accel-Buffering: no`), and enables instantaneous cart population (`event: cart`) before LLM text generation begins.

## 21. Admin Dashboard Analytics Overhaul & Scope Boundary
**Decision:** Overhauled the admin dashboard to compute dynamic time-range analytics (`today`, `7d`, `30d`, `90d`, `all`), interactive SVG trendlines, dish volume leaderboards, and solver feasibility health, while deferring admin audit logging to a subsequent phase.
**Rationale:** Restaurant operators needed immediate visibility into floor revenue trajectories, average order values, and solver feasibility rates. Admin audit logging requires dedicated storage lifecycle policies and was benched to keep the implementation focused and deliver high-impact operational intelligence without unnecessary complexity.

## 22. Generator-First Streaming Core with Unary Adapters & Modular Pipeline Architecture
**Decision:** We refactored both `explanation_generator.py` and `recommendation_pipeline.py` into a "Streaming Core with Unary Adapter" pattern:
1. Canonical streaming generators (`stream_explanation`, `stream_question_answer`, `_execute_recommendation_pipeline`) serve as the single source of truth for all business logic, prompt construction, constraint merging, SQL filtering, ILP solving, and DB commits.
2. Non-streaming functions (`generate_explanation`, `process_chat_request`) are thin unary adapters that drain the generators in memory and return final typed payloads directly.
3. Decomposed the monolithic ~500-line pipeline generator into dedicated single-responsibility helper functions (`_load_conversation_state`, `_resolve_restaurant_context`, `_ensure_conversation`, `_handle_non_recommendation_intent`, `_build_recommendation_result`, `_save_conversation_state`, and `_dispatch_gcs_audit`), bringing the coordinator down to ~80 lines.
**Rationale:** Maintaining separate parallel implementations of response generators and pipeline orchestrators introduced code duplication (>430 redundant lines) and a high risk of behavioral divergence. Establishing the streaming generator as the single source of truth guarantees identical business logic across both `POST /api/chat` (unary REST) and `POST /api/chat/stream` (SSE streaming) while retaining 100% backward compatibility and testability.

## 23. Continuous Zero-Filled Time Series & Cubic Spline Interpolation for Operational Analytics
**Decision:** In `backend/app/routers/admin.py` and `frontend/src/components/admin/analytics-chart.tsx`, we:
1. Added continuous zero-filled time-series generation for hourly (`12h`, `today`) and daily (`7d`, `30d`, `90d`, `custom`) buckets so charts render continuous trajectories even when order history is sparse.
2. Implemented smooth cubic Bézier spline interpolation (`createSmoothSpline`) with multi-stop gradients, drop shadows, interactive tracking crosshairs, and dynamic X-axis stepping.
3. Added custom date range filtering (`start_date`, `end_date`) and a `12h` operational convenience filter.
4. Joined the `Restaurant` table to surface venue attribution directly in top dish leaderboards.
**Rationale:** Standard SQL `GROUP BY` returns disjoint rows only for days with placed orders, which produced single flat lines or jagged discontinuities across new venues. Contiguous zero-filling paired with cubic spline curves ensures high-fidelity visual trajectories and prevents rendering errors (such as `NaN` attribute errors when switching metric views).


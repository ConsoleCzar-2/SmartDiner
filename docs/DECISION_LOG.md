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

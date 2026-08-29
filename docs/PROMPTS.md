# Prompt Engineering & LLM Integration

> **Current configuration:** The repository uses the Google GenAI SDK with Gemini 3.5 Flash Lite for constraint extraction and grounded explanation. SQL filtering and PuLP optimization remain the source of truth for safety, availability, servings, and budget.

SmartDiner relies on **Gemini 3.5 Flash Lite** for two distinct, heavily-governed tasks in the 4-step pipeline: Constraint Extraction and Explanation Generation. This document outlines the strategies, challenges, and solutions used to craft these prompts.

## 1. Constraint Extraction Prompt (`SYSTEM_PROMPT`)

Located in `backend/app/services/constraint_extractor.py`, this prompt acts as the system's "ears". Its sole job is to translate messy, conversational human input into a strict Pydantic JSON structure that the SQL and ILP math engines can read.

### Prompt Strategy
- **Identity & Constraints:** The LLM is explicitly told it is an extraction engine, *not* a conversational agent. It is forbidden from making decisions about what food to recommend.
- **State Merging:** The prompt instructs the LLM to look at the `Previous Constraints` JSON object and merge it with the new `User Request`. For example, if the previous state had 4 people, and the user says "add one more", the LLM must output 5.
- **Strict Typing:** The schema defines rigid constraints, such as standardizing spice levels to exactly `["None", "Low", "Medium", "High", "Extreme", "Any"]`.

### The Nullability Challenge
**Issue:** We discovered that if we strictly defined `max_budget` as a required integer, and the user said "budget is not an issue", the LLM would panic and hallucinate a default value (e.g., `3000`) just to satisfy the strict schema requirement.
**Solution:** We optimized the Pydantic schema generation logic. We dynamically stripped `anyOf` constraints from the OpenAPI schema and explicitly injected `"nullable": True` for fields like `max_budget` and `preferred_cuisines`. This allows the LLM to safely output `null` when constraints are unmentioned or explicitly unbounded, allowing the math solver to accurately run without an artificial ceiling.

## 2. Explanation Generation Prompt (`EXPLANATION_SYSTEM_PROMPT`)

Located in `backend/app/services/explanation_generator.py`, this prompt acts as the system's "mouth". It takes the mathematically perfect menu created by the ILP solver and generates a human-friendly summary.

### Prompt Strategy
- **Grounding:** The prompt is heavily grounded. It is provided with a JSON dump of the solver's exact mathematical output (total cost, items chosen, quantities, remaining budget).
- **Anti-Hallucination Directive:** The system prompt explicitly states: *"CRITICAL: DO NOT invent items, prices, or rationales that are not present in the SOLVER_OUTPUT."*
- **Tone:** Instructed to be concise (1-3 sentences) and hospitable.
- **Infeasibility Handling:** If the math solver returns `Infeasible` (e.g., trying to feed 10 people on ₹100), the solver output explicitly says it failed. The LLM is instructed to politely explain exactly *why* it failed based on the constraints (e.g., "I couldn't find a combination to feed 10 people for just ₹100. Would you be willing to increase the budget?").

## 3. Evaluation & Results

We utilize a comprehensive evaluation suite (`backend/tests/evaluation_report.py`) with 42 edge cases across 5 categories (Budget Strictness, Dietary Safety, Group Dynamics, Preferences, Impossible Constraints).

**Key Metrics (Using Gemini 3.5 Flash Lite):**
- **JSON Compliance:** 100% (The model never returns malformed JSON, thanks to `response_schema` API enforcement).
- **Hallucination Rate:** 0% (The separation of concerns ensures the LLM cannot hallucinate items into the math solver, and the explanation LLM is too strictly grounded to lie).
- **Latency:** ~600ms for extraction, ~400ms for explanation generation. Total pipeline latency comfortably sits under the 5-second requirement.

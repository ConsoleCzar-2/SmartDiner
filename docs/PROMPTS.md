# Prompt Engineering & LLM Integration

> **Current configuration:** The repository uses the Google GenAI SDK with Gemini 3.5 Flash Lite for constraint extraction and grounded explanation. SQL filtering and PuLP optimization remain the source of truth for safety, availability, servings, and budget.

SmartDiner relies on **Gemini 3.5 Flash Lite** for three distinct, heavily-governed tasks in the pipeline: Intent Classification, Constraint Extraction, and Explanation/Answer Generation. This document outlines the strategies, challenges, and solutions used to craft these prompts.

## 1. Intent Classification Prompt (`INTENT_CLASSIFICATION_PROMPT`)

Located in `backend/app/prompts/intent_classification.py`, this acts as the front-line routing and security layer.
- **Goal**: Classify the user's message into `ORDER`, `MODIFICATION`, `QUESTION`, `GREETING`, `OFF_TOPIC`, or `ADVERSARIAL`.
- **Short-Circuiting**: By isolating intent early, the system can instantly reject adversarial prompts, or route `QUESTION` intents directly to a lightweight Q&A LLM call without running the heavy SQL/ILP mathematical pipeline.
- **Output**: Strict JSON containing `intent` and `reason`.

## 2. Constraint Extraction Prompt (`SYSTEM_PROMPT`)

Located in `backend/app/prompts/constraint_extraction.py`, this prompt acts as the system's "ears" for orders and modifications. Its sole job is to translate messy, conversational human input into a strict Pydantic JSON structure that the SQL and ILP math engines can read.

### Prompt Strategy
- **Identity & Constraints:** The LLM is explicitly told it is an extraction engine, *not* a conversational agent. It is forbidden from making decisions about what food to recommend.
- **State Merging (Deltas):** The prompt instructs the LLM to look at the `Existing Constraints` JSON object and merge it with the new `User Request`, returning *only* the modified fields.
- **Context-Aware Swapping (Rule 11):** The LLM is provided the `Current Draft Cart`. If the user asks to "remove the paneer and add a beverage", the LLM uses this context to populate the `excluded_dishes` and `preferred_categories` arrays accurately.
- **Strict Typing:** The schema defines rigid constraints, such as standardizing spice levels to exactly `["None", "Low", "Medium", "High", "Extreme", "Any"]`.

### The Nullability Challenge
**Issue:** We discovered that if we strictly defined `max_budget` as a required integer, and the user said "budget is not an issue", the LLM would panic and hallucinate a default value (e.g., `3000`) just to satisfy the strict schema requirement.
**Solution:** We optimized the Pydantic schema generation logic. We dynamically stripped `anyOf` constraints from the OpenAPI schema and explicitly injected `"nullable": True` for fields like `max_budget` and `preferred_cuisines`. This allows the LLM to safely output `null` when constraints are unmentioned or explicitly unbounded, allowing the math solver to accurately run without an artificial ceiling.

## 3. Explanation & Answer Generation Prompts

Located in `backend/app/services/explanation_generator.py`, these prompts act as the system's "mouth".

### Order Explanations (`EXPLANATION_SYSTEM_PROMPT`)
- **Grounding:** The prompt is heavily grounded. It is provided with a JSON dump of the solver's exact mathematical output (total cost, items chosen, quantities, remaining budget).
- **Anti-Hallucination Directive:** The system prompt explicitly states: *"CRITICAL: DO NOT invent items, prices, or rationales that are not present in the SOLVER_OUTPUT."*

### Conversational Answers (`generate_question_answer`)
- When the Intent Classifier flags a `QUESTION` (e.g. "what exactly did you change?"), this lightweight prompt receives the `Current Draft Cart` and the `Conversation History`.
- It answers the user contextually without modifying the order or invoking the mathematical solver.
- **Tone:** Instructed to be concise (1-3 sentences) and hospitable.
- **Infeasibility Handling:** If the math solver returns `Infeasible` (e.g., trying to feed 10 people on ₹100), the solver output explicitly says it failed. The LLM is instructed to politely explain exactly *why* it failed based on the constraints (e.g., "I couldn't find a combination to feed 10 people for just ₹100. Would you be willing to increase the budget?").

## 4. Admin AI Insights Prompt (`ADMIN_INSIGHTS_SYSTEM_PROMPT`)

Located in `backend/app/prompts/admin_insights_prompt.py`, this prompt powers the executive business intelligence chat interface (`/admin/insights`).

### Prompt Strategy
- **Dual-Source Ingestion:** Ingests live aggregated PostgreSQL metrics (revenue sums, orders count, top dishes, active restaurants) and GCS WORM audit log summaries (solver statuses, token burn, latency percentiles).
- **Strict Grounding:** Mandates that every operational claim must cite the provided context. If data is not available, the model must explicitly state the limitation rather than estimating.
- **Currency Compliance:** Explicitly enforces Indian Rupee (`₹` / INR) notation for all revenue and monetary figures.
- **Zero-Emoji Directive:** Strictly forbids emojis to maintain an executive audit-grade communication standard.
- **Structured Markdown:** Enforces headers, markdown tables, bullet points, and code blocks for high scannability.

## 5. Universal Markdown & Zero-Emoji Communication Standard

Across all AI prompts in the SmartDiner platform (`constraint_extraction.py`, `explanation.py`, `admin_insights_prompt.py`):
1. **Markdown Formatting:** All prompts instruct the model to produce standard GitHub-flavored markdown. The frontend renders this safely through `frontend/src/components/ui/markdown-content.tsx`.
2. **Zero-Emoji Policy:** System prompts explicitly prohibit emoji usage (e.g., smiles, food emojis, sparkles). Only standard colored badge UI elements rendered natively by the frontend are permitted where necessary.
3. **Currency Grounding:** All financial quantities are grounded in INR (`₹`), preventing hallucinated foreign currency symbols.

## 6. Evaluation & Results

We utilize a comprehensive automated evaluation suite (`backend/tests/test_llm_accuracy.py` and `backend/tests/test_llm_judge.py`) with 50 golden cases and qualitative LLM-as-a-judge scoring.

**Key Metrics (Using Gemini 3.5 Flash Lite):**
- **JSON Compliance:** 100% (The model never returns malformed JSON, thanks to `response_schema` API enforcement).
- **Hallucination Rate:** 0.0% (The separation of concerns ensures the LLM cannot hallucinate items into the math solver, and explanation prompts are strictly grounded in solver outputs).
- **Extraction Accuracy:** 100.0% across 15 representative golden test suites.
- **Latency:** ~600ms for extraction, ~400ms for explanation generation. Total pipeline latency comfortably sits under the 5-second requirement.


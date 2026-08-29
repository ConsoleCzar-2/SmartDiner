# Product Requirements Document (PRD)


## 1. Introduction & Problem Statement
Dining out with large groups or individuals with specific dietary constraints (e.g., severe allergies, strict veganism, or specific spice tolerances) is often a stressful and fragmented experience. Customers frequently have to scrutinize menus, interrogate servers, and manually calculate costs to ensure everyone is fed within a budget. Furthermore, for those with severe allergies, a simple miscommunication can lead to dangerous health risks. 

SmartDiner is designed to bridge this gap. It is an AI-powered, deterministic restaurant concierge. Unlike generic AI chatbots that are prone to hallucination—recommending dishes that don't exist, miscalculating prices, or failing to recognize allergens—SmartDiner uses a strictly governed architecture. It combines the conversational flexibility of Large Language Models (LLMs) with the absolute mathematical certainty of Integer Linear Programming (ILP) and relational databases.

## 2. Target Personas
1. **The Planner (Customer):** Wants to quickly find a safe, delicious, and budget-friendly combination of food for their table without having to do the math or worry about accidentally ordering an allergen.
2. **The Diner (Customer):** Wants to visually browse the menu and trust that the recommendations made to them are 100% safe to eat.
3. **Restaurant Staff / Manager:** Needs a dashboard to monitor live AI-generated orders, review conversation audit logs for quality assurance, and track revenue metrics without needing deep technical knowledge.

## 3. Key Features & Capabilities

### 3.1. Governed AI Concierge
- **Natural Language Input:** Customers can type complex constraints naturally (e.g., "Food for 5, 2 vegetarians, no dairy, budget is ₹3000").
- **Zero Hallucination Guarantee:** The system must never recommend an item that is out of stock, exceeds the budget, or contains an excluded allergen.
- **Mathematical Optimization:** The system automatically maximizes the overall "value" of the order (rating × serving size) while strictly adhering to all user constraints.

### 3.2. Visual Menu Browser
- Customers can visually browse the restaurant's offerings categorized by type (e.g., Starters, Main Course, Beverages).
- Items must display clear dietary tags (Vegetarian/Vegan/Non-Vegetarian) and spice level indicators.

### 3.3. Restaurant Admin Dashboard
- **Real-Time Metrics:** Admins can view active orders, total revenue, and veg vs. non-veg breakdowns.
- **Audit Logs:** Full transparency into customer-AI conversations, showing exactly what constraints the LLM extracted and what the ILP solver outputted.

## 4. System Requirements

### 4.1. Functional Requirements
- **Constraint Extraction:** The system must accurately extract at least 10 dimensions of constraints (party size, veg/non-veg split, budget, allergens, spice tolerance, cuisines, categories, specific dishes, and modification flags) from natural language.
- **Allergen Tracing:** Allergens must be mapped at the ingredient level, not the dish level, to ensure a single source of truth for safety.
- **ILP Constraints:** The optimization engine must guarantee that total cost ≤ budget, and total servings ≥ party size.

### 4.2. Non-Functional Requirements
- **Performance:** The end-to-end pipeline (Extraction → DB Filter → ILP Solver → Explanation) must resolve in under 5 seconds to maintain a conversational feel.
- **Scalability:** The architecture must cleanly separate state (PostgreSQL) from compute (FastAPI/Cloud Run), allowing for horizontal scaling.
- **Cost Efficiency:** The AI layer should utilize lightweight, high-throughput models (e.g., Gemini 3.5 Flash Lite) to ensure the per-transaction cost remains negligible.

## 5. Success Metrics
- **Constraint Accuracy:** The LLM must correctly parse >95% of numerical and categorical constraints.
- **Solver Feasibility Rate:** The ILP solver must successfully find a menu or gracefully decline an impossible request 100% of the time, without crashing.
- **Zero-Incident Safety:** 100% accuracy in filtering out requested allergens from the candidate pool before optimization.

## 6. Future Scope
- Payment processing and direct point-of-sale (POS) integration.
- Delivery logistics and driver tracking.
- Multi-restaurant cart combinations (orders are strictly scoped to a single restaurant ID).

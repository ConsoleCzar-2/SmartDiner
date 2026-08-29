# Welcome to the SmartDiner Wiki

**SmartDiner** is an AI-powered restaurant assistant that mathematically guarantees allergen safety, budget compliance, and dietary adherence through a strictly governed architecture.

Unlike traditional LLM chatbots that hallucinate prices or forget fatal allergies, SmartDiner separates natural language understanding from deterministic business logic, achieving a 100% safety and compliance rate.

## Table of Contents

This Wiki serves as the comprehensive documentation for the engineering, architecture, and product decisions behind SmartDiner.

- [**Product Requirements Document (PRD)**](https://github.com/ConsoleCzar-2/SmartDiner/wiki/PRD)
  The core feature set, target personas, and success metrics that define the SmartDiner MVP.

- [**Architecture & Pipeline Design**](https://github.com/ConsoleCzar-2/SmartDiner/wiki/ARCHITECTURE)
  A deep dive into the 4-step governed pipeline (LLM → SQL → ILP Solver → LLM) and the system topology.

- [**Database & ERD**](https://github.com/ConsoleCzar-2/SmartDiner/wiki/DATABASE)
  Explanation of our strict normalized PostgreSQL schema, UUIDv7 strategy, and how allergen safety is enforced via ingredients.

- [**REST API Reference**](https://github.com/ConsoleCzar-2/SmartDiner/wiki/API)
  Documentation of the FastAPI HTTP surface, including the main conversational endpoint and admin routes.

- [**Prompt Engineering & LLM Integration**](https://github.com/ConsoleCzar-2/SmartDiner/wiki/PROMPTS)
  Details on how Gemini 3.5 Flash Lite is constrained via structured JSON, few-shot prompting, and state merging.

- [**Engineering Decision Log**](https://github.com/ConsoleCzar-2/SmartDiner/wiki/DECISION_LOG)
  A historical record of the critical technical choices made, alternative architectures rejected, and the rationale behind them.

## Quick Start

If you're looking to run the project locally or view the source code, please refer to the main repository `README.md`:

[**View the Source Code on GitHub**](https://github.com/ConsoleCzar-2/SmartDiner)

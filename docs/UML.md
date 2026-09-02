# SmartDiner UML Diagrams

While the ER Diagram covers the relational database structure, these UML Class and Sequence diagrams illustrate the object-oriented structure of the Python backend (SQLAlchemy Models and Pydantic Schemas) and the execution flow of the governed AI pipeline.

## 1. Overall System Architecture & Separation of Concerns

This flowchart outlines the high-level architecture of the Governed Recommendation Pipeline. Note how the **Gemini 3.5 Flash Lite** model is specifically orchestrated across multiple independent tasks (Intent Classification, Constraint Extraction, Question Answering, and Explanation).

**Why is the `QUESTION` intent separated?**
By isolating conversational questions (e.g., "What did you change?") from the main constraint extraction flow, we can short-circuit the pipeline. This bypasses the heavy SQL filtering and ILP math solver entirely, providing a much faster response time and guaranteeing that the user's ongoing draft cart is not accidentally wiped out or modified by the solver when they are simply asking for clarification.

```mermaid
flowchart TD
    Client[Next.js Client] -->|API Request| FastAPI[FastAPI Backend]
    FastAPI --> Pipeline[Governed Recommendation Pipeline]
    
    subgraph Pipeline [Governed Recommendation Pipeline]
        direction TB
        Int[0.5 Intent Classifier]
        Ext[1. LLM Constraint Extractor]
        Merge[1.5 State Merger]
        DBF[2. PostgreSQL Menu Filter]
        ILP[3. PuLP Integer Linear Solver]
        Exp[4. LLM Explanation Generator]
        Ans[Question Answerer]
        
        Int & Ext -.->|Concurrent| Merge
        Int -->|QUESTION| Ans
        Merge -->|Extracted JSON| DBF
        DBF -->|Safe Candidate Items| ILP
        ILP -->|Mathematically Optimal Menu| Exp
    end
    
    Pipeline -.->|Response| FastAPI
    FastAPI -.->|JSON| Client
    
    %% AI Models mapping
    Gemini[Gemini 3.5 Flash Lite]
    Int <-->|Temp: 0.0| Gemini
    Ext <-->|Temp: 0.1| Gemini
    Ans <-->|Temp: 0.3| Gemini
    Exp <-->|Temp: 0.3| Gemini
    
    DBF <--> DB[(PostgreSQL 16)]
```

## 2. Class Diagram (Core Backend Models & Schemas)

This diagram shows how the FastAPI Pydantic schemas (for data validation) map and relate to the internal SQLAlchemy ORM models.

```mermaid
classDiagram
    %% SQLAlchemy Models
    class Restaurant {
        +UUID id
        +String name
        +String cuisine_type
        +Boolean is_active
        +get_menu()
    }
    
    class User {
        +UUID id
        +String name
        +JSONB default_preferences
        +get_orders()
    }
    
    class MenuItem {
        +UUID id
        +UUID restaurant_id
        +String name
        +Numeric price
        +String dietary_preference
        +String spice_level
        +Integer serving_size
        +Boolean is_available
    }
    
    class Conversation {
        +UUID id
        +UUID user_id
        +UUID restaurant_id
        +JSONB messages
        +JSONB current_constraints
        +JSONB current_cart
    }
    
    %% Pydantic Schemas
    class ChatRequest {
        +String message
        +UUID restaurant_id
        +UUID conversation_id
    }
    
    class ExtractedConstraints {
        +Integer people_count
        +Integer vegetarian_count
        +Float max_budget
        +String max_spice_level
        +List allergens
    }
    
    class RecommendedItem {
        +UUID id
        +String name
        +Integer quantity
        +Float unit_price
        +Float subtotal
        +Integer total_servings
    }
    
    class ChatResponse {
        +UUID conversation_id
        +RecommendationResult recommendation
        +String explanation
        +ExtractedConstraints extracted_constraints
    }
    
    %% Relationships
    Restaurant "1" *-- "many" MenuItem : contains
    User "1" *-- "many" Conversation : has
    ChatRequest ..> ExtractedConstraints : triggers extraction
    ExtractedConstraints ..> MenuItem : filters (SQL)
    MenuItem ..> RecommendedItem : converted to
    ChatResponse *-- RecommendedItem : contains
```

## 3. Sequence Diagram (Chat Execution Flow)

This sequence diagram illustrates the governed AI pipeline, showing the new concurrent classification/extraction and short-circuit logic for conversational questions.

```mermaid
sequenceDiagram
    actor Client
    participant API as FastAPI Router
    participant LLM1 as Gemini (Intent)
    participant LLM2 as Gemini (Extractor)
    participant DB as PostgreSQL
    participant ILP as PuLP Solver
    participant LLM3 as Gemini (Explainer/QA)
    participant GCS as Cloud Storage (WORM)

    Client->>API: POST /api/chat {message, restaurant_id}
    
    par Concurrent AI Tasks
        API->>LLM1: Classify Intent
        LLM1-->>API: Intent (e.g. ORDER, QUESTION)
    and
        API->>LLM2: Extract Constraints (Prompt + Schema)
        LLM2-->>API: ExtractedConstraints JSON
    end
    
    alt is QUESTION
        API->>LLM3: Generate QA Response based on Draft Cart
        LLM3-->>API: Conversational Answer
        API-->>Client: ChatResponse (Unmodified Cart)
    else is ORDER or MODIFICATION
        API->>DB: Query MenuItems WHERE (price, allergens, spice)
        DB-->>API: List[MenuItem] (Safe Candidates)
        
        API->>ILP: Optimize(Safe Candidates, Constraints)
        ILP-->>API: Optimal Cart & Quantities
        
        API->>LLM3: Generate Grounded Explanation
        LLM3-->>API: 2-Sentence Summary
        
        API-->>Client: ChatResponse JSON
        
        %% Background task for compliance
        API-)GCS: Upload Cryptographic Audit Log (Background)
    end
```

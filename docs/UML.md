# SmartDiner UML Diagrams

While the ER Diagram covers the relational database structure, these UML Class and Sequence diagrams illustrate the object-oriented structure of the Python backend (SQLAlchemy Models and Pydantic Schemas) and the execution flow of the governed AI pipeline.

## 1. Class Diagram (Core Backend Models & Schemas)

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

## 2. Sequence Diagram (Chat Execution Flow)

This sequence diagram illustrates the strict 4-step pipeline that prevents LLM hallucinations.

```mermaid
sequenceDiagram
    actor Client
    participant API as FastAPI Router
    participant LLM1 as Gemini (Extractor)
    participant DB as PostgreSQL
    participant ILP as PuLP Solver
    participant LLM2 as Gemini (Explainer)
    participant GCS as Cloud Storage (WORM)

    Client->>API: POST /api/chat {message, restaurant_id}
    API->>LLM1: Extract Constraints (Prompt + Schema)
    LLM1-->>API: ExtractedConstraints JSON
    
    API->>DB: Query MenuItems WHERE (price, allergens, spice)
    DB-->>API: List[MenuItem] (Safe Candidates)
    
    API->>ILP: Optimize(Safe Candidates, Constraints)
    ILP-->>API: Optimal Cart & Quantities
    
    API->>LLM2: Generate Grounded Explanation
    LLM2-->>API: 2-Sentence Summary
    
    API-->>Client: ChatResponse JSON
    
    %% Background task for compliance
    API-)GCS: Upload Cryptographic Audit Log (Background)
```

# SmartDiner UML Diagrams

While the ER Diagram covers the relational database structure, these UML Class and Sequence diagrams illustrate the object-oriented structure of the Python backend (SQLAlchemy Models and Pydantic Schemas), the Generator-First streaming architecture, and the execution flows for both REST and Server-Sent Events (SSE).

## 1. Overall System Architecture & Separation of Concerns

This flowchart outlines the high-level architecture of the Governed Recommendation Pipeline. Note how the **Gemini 3.5 Flash Lite** model is specifically orchestrated across independent tasks (Intent Classification, Constraint Extraction, Question Answering, and Explanation).

The recommendation engine adopts a **Generator-First Architecture**: `_execute_recommendation_pipeline` serves as the canonical async generator. `stream_chat_pipeline` yields SSE text frames to `POST /api/chat/stream`, while `process_chat_request` drains the generator in memory to assemble the JSON payload for `POST /api/chat`.

```mermaid
flowchart TD
    Client[Next.js Client] -->|POST /api/chat/stream (SSE)| SSEAPI[FastAPI SSE Router]
    Client -->|POST /api/chat (REST)| UnaryAPI[FastAPI REST Router]
    
    SSEAPI --> StreamAdapter[stream_chat_pipeline<br/>SSE Text Formatter]
    UnaryAPI --> UnaryAdapter[process_chat_request<br/>In-Memory Drain Adapter]
    
    StreamAdapter --> CoreGen[_execute_recommendation_pipeline<br/>Canonical Async Generator]
    UnaryAdapter --> CoreGen
    
    subgraph ModularPipeline [Decomposed Pipeline Stages]
        direction TB
        S1["1. _load_conversation_state<br/>(PostgreSQL JSONB)"]
        S2["2. _resolve_restaurant_context<br/>(Alias matching, venue switching, reset)"]
        S3["3. Concurrent Intent & Extraction<br/>(Gemini 3.5 Flash Lite)"]
        S4["4. _handle_non_recommendation_intent<br/>(QUESTION / GREETING / OFF_TOPIC short-circuit)"]
        S5["5. SQL Menu Filter<br/>(L1 / L2 Cache + Allergen subquery)"]
        S6["6. PuLP ILP Solver<br/>(Deterministic Knapsack Optimization)"]
        S7["7. _build_recommendation_result<br/>(Typed items & dietary counts)"]
        S8["8. LLM Explanation Streamer<br/>(stream_explanation generator)"]
        S9["9. _save_conversation_state<br/>(Commit to DB)"]
        S10["10. _dispatch_gcs_audit<br/>(Async GCS WORM Upload)"]
        
        S1 --> S2 --> S3 --> S4
        S4 -->|ORDER / MODIFICATION| S5 --> S6 --> S7 --> S8 --> S9 --> S10
        S4 -->|QUESTION / GREETING| S9 --> S10
    end
    
    CoreGen --> ModularPipeline
    CoreGen -.->|event: status / cart / token / done| StreamAdapter
    CoreGen -.->|yields chunks| UnaryAdapter
```

## 2. Class Diagram (Core Backend Models & Schemas)

This diagram shows how the FastAPI Pydantic schemas (for data validation) map and relate to internal SQLAlchemy ORM models.

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
        +Integer vegan_count
        +Integer non_vegetarian_count
        +Float max_budget
        +String max_spice_level
        +List excluded_allergens
        +List preferred_cuisines
        +List preferred_categories
        +List specific_dish_requests
        +List excluded_dishes
    }
    
    class RecommendedItem {
        +UUID id
        +String name
        +Integer quantity
        +Float unit_price
        +Float subtotal
        +Integer total_servings
        +String category
        +String dietary_preference
    }
    
    class TopDishItem {
        +String name
        +String restaurant_name
        +String category
        +Integer quantity_sold
        +Float revenue
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

## 3. Sequence Diagram (Unary REST Execution Flow: `POST /api/chat`)

This sequence diagram illustrates the unary HTTP request flow via `process_chat_request`, which drains the canonical generator in memory and returns a complete `ChatResponse` JSON payload.

```mermaid
sequenceDiagram
    actor Client
    participant API as FastAPI Router (/api/chat)
    participant Pipe as process_chat_request (Unary Adapter)
    participant Gen as _execute_recommendation_pipeline
    participant DB as PostgreSQL 16
    participant ILP as PuLP CBC Solver
    participant LLM as Gemini 3.5 Flash Lite
    participant GCS as Cloud Storage (WORM)

    Client->>API: POST /api/chat {message, restaurant_id}
    API->>Pipe: process_chat_request(request, db)
    Pipe->>Gen: Drain _execute_recommendation_pipeline()
    
    Gen->>DB: Load Conversation & History
    DB-->>Gen: Conversation State
    
    par Concurrent Intent & Extraction
        Gen->>LLM: Classify Intent
        LLM-->>Gen: IntentResult
    and
        Gen->>LLM: Extract Constraints (Prompt + Schema)
        LLM-->>Gen: ExtractedConstraints
    end
    
    alt Intent is QUESTION / GREETING
        Gen->>LLM: Answer Query using Draft Cart Context
        LLM-->>Gen: Conversational Text
    else Intent is ORDER / MODIFICATION
        Gen->>DB: Query MenuItems (Allergen subquery + cache)
        DB-->>Gen: Safe Candidate Dishes
        Gen->>ILP: Optimize(Candidates, Constraints)
        ILP-->>Gen: Optimal Quantities
        Gen->>LLM: Stream Explanation Tokens (drained into full text)
        LLM-->>Gen: Grounded Text
    end
    
    Gen->>DB: Save Messages, Cart, & Constraints (Commit)
    Gen-->>Pipe: Yield final done payload
    Pipe-->>API: ChatResponse JSON
    API-->>Client: 200 OK (ChatResponse)
    
    API-)GCS: Upload Audit Log via BackgroundTasks
```

## 4. Sequence Diagram (Server-Sent Events Streaming Flow: `POST /api/chat/stream`)

This sequence diagram illustrates real-time event streaming via `stream_chat_pipeline`. The user receives phase status updates, and crucially, the **verified cart is rendered immediately upon ILP completion** before explanation tokens stream chunk-by-chunk.

```mermaid
sequenceDiagram
    actor Client
    participant API as FastAPI SSE Router (/api/chat/stream)
    participant Pipe as stream_chat_pipeline (SSE Adapter)
    participant Gen as _execute_recommendation_pipeline
    participant DB as PostgreSQL 16
    participant ILP as PuLP CBC Solver
    participant LLM as Gemini 3.5 Flash Lite
    participant GCS as Cloud Storage (WORM)

    Client->>API: POST /api/chat/stream {message, restaurant_id}
    API-->>Client: 200 OK (text/event-stream)
    API->>Pipe: stream_chat_pipeline(request, db)
    Pipe->>Gen: Iterate _execute_recommendation_pipeline()

    Gen-->>Pipe: { type: "status", step: "intent_and_constraints" }
    Pipe-->>Client: event: status\ndata: {"step": "intent_and_constraints"}\n\n

    par Concurrent Intent & Extraction
        Gen->>LLM: Classify Intent
        LLM-->>Gen: IntentResult
    and
        Gen->>LLM: Extract Constraints
        LLM-->>Gen: ExtractedConstraints
    end

    Gen-->>Pipe: { type: "status", step: "filtering_menu" }
    Pipe-->>Client: event: status\ndata: {"step": "filtering_menu"}\n\n
    Gen->>DB: Query MenuItems (Allergen & Price Filters)
    DB-->>Gen: Safe Candidates

    Gen-->>Pipe: { type: "status", step: "optimizing_meal" }
    Pipe-->>Client: event: status\ndata: {"step": "optimizing_meal"}\n\n
    Gen->>ILP: Solve ILP Knapsack Formulation
    ILP-->>Gen: Optimal Selection

    %% IMMEDIATE CART HYDRATION
    Gen-->>Pipe: { type: "cart", recommendation: RecommendationResult }
    Pipe-->>Client: event: cart\ndata: {"recommendation": {...}}\n\n
    Note over Client: Cart drawer hydrates immediately!<br/>User sees chosen dishes and budget in INR.

    Gen-->>Pipe: { type: "status", step: "generating_explanation" }
    Pipe-->>Client: event: status\ndata: {"step": "generating_explanation"}\n\n

    Gen->>LLM: stream_explanation(client.aio.models.generate_content_stream)
    loop For each text chunk
        LLM-->>Gen: Text Chunk
        Gen-->>Pipe: { type: "token", content: chunk }
        Pipe-->>Client: event: token\ndata: {"content": chunk}\n\n
    end

    Gen->>DB: Commit Messages, Constraints, & Cart
    Gen-->>Pipe: { type: "done", response: ChatResponse, telemetry: {...} }
    Pipe-->>Client: event: done\ndata: {"response": {...}}\n\n

    Gen-)GCS: asyncio.create_task(upload_audit_log_to_gcs(...))
```

# API Documentation

The SmartDiner backend exposes a RESTful API powered by FastAPI.

## Base URL
All API requests are routed through `/api`. Locally, the base URL is `http://localhost:8000/api`; the deployed base URL is `https://smartdiner-backend.onrender.com/api`.

The frontend reads `NEXT_PUBLIC_API_URL` at build time and supports the legacy `NEXT_PUBLIC_API_BASE_URL`. Backend CORS must allow the exact Vercel origin.

---

## 1. Chat & Recommendation Engine

### `POST /api/chat`
Processes natural language input from the customer, updates conversation state, and returns a mathematically verified menu recommendation.

#### Request Body
```json
{
  "restaurant_id": "01a03c12-0f10-79cc-ae4f-6f32ca7a29b8",
  "user_id": "01a03c12-0f10-79cc-ae4f-6f32ca7a29b9",
  "conversation_id": "01a03c12-0f10-79cc-ae4f-6f32ca7a29b0", 
  "message": "We have 4 people, 1 is strictly vegetarian, nobody can eat peanuts. Budget is 4000 total."
}
```
*Note: `restaurant_id` is optional. When omitted or null, the request runs in **Restaurant-Agnostic Concierge Mode**, dynamically searching across candidate restaurants and returning cross-restaurant comparison metadata. If `conversation_id` is omitted or null, a new conversation state is instantiated.*

#### Success Response (200 OK)
```json
{
  "conversation_id": "01a03c12-0f10-79cc-ae4f-6f32ca7a29b0",
  "restaurant_id": "01a03c12-0f10-79cc-ae4f-6f32ca7a29b8",
  "restaurant_name": "Spice Garden",
  "status": "Optimal",
  "reason": "Here is a safe, optimal feast for 4 that keeps you completely peanut-free while respecting your budget!",
  "computed_total": 3850,
  "budget_remaining": 150,
  "total_servings": 9,
  "veg_servings": 3,
  "nonveg_servings": 6,
  "items": [
    {
      "id": "01a03c12-0f10-79cc-ae4f-6f32ca7a29c1",
      "name": "Grilled Salmon",
      "category": "Main Course",
      "spice_level": "Low",
      "dietary_preference": "Non-Vegetarian",
      "quantity": 2,
      "subtotal": 2400,
      "total_servings": 4
    }
  ],
  "cross_restaurant_meta": {
    "is_cross_restaurant": true,
    "top_candidates": [
      {
        "restaurant_id": "01a03c12-0f10-79cc-ae4f-6f32ca7a29b8",
        "restaurant_name": "Spice Garden",
        "cuisine": "North Indian",
        "rating": 4.8,
        "sample_dishes": ["Butter Chicken", "Dal Makhani"],
        "match_score": 95
      }
    ]
  }
}
```

#### Error Response (400 Bad Request)
Returned when the ILP solver confirms no mathematical combination of items exists to satisfy the constraints.
```json
{
  "conversation_id": "01a03c12-0f10-79cc-ae4f-6f32ca7a29b0",
  "status": "Infeasible",
  "reason": "I couldn't find a menu combination that fits a ₹100 budget for 4 people. Would you be willing to raise the budget to ₹1500?",
  "computed_total": 0,
  "budget_remaining": null,
  "total_servings": 0,
  "veg_servings": 0,
  "nonveg_servings": 0,
  "items": []
}
```

### `POST /api/chat/stream`
Real-time streaming recommendation endpoint powered by Server-Sent Events (SSE). Streams pipeline progress status, dispatches the verified recommendation cart immediately upon ILP solver completion, and streams grounded explanation tokens progressively from Gemini 3.5 Flash Lite.

#### Media Type
`text/event-stream`

#### Headers
- `Cache-Control`: `no-cache`
- `Connection`: `keep-alive`
- `X-Accel-Buffering`: `no`

#### Event Types
1. **`event: status`**: Dispatched during pipeline phase transitions.
   ```json
   { "step": "filtering_menu", "message": "Filtering menu items by allergens, dietary preferences, and availability..." }
   ```
2. **`event: cart`**: Dispatched immediately when the ILP solver computes the optimal combination.
   ```json
   { "recommendation": { "status": "Optimal", "items": [ ... ], "computed_total": 1420.0, ... } }
   ```
3. **`event: token`**: Incremental natural-language explanation token chunk.
   ```json
   { "content": "Here is a safe, optimal combination..." }
   ```
4. **`event: done`**: Dispatched upon completion with the full response and telemetry payload.
   ```json
   { "response": { "conversation_id": "...", ... }, "telemetry": { ... } }
   ```

### `GET /api/chat/active`
Retrieves the most recent active conversation for the user at a given restaurant, allowing the frontend to seamlessly restore the chat history, constraints, and the live draft cart after a page refresh.

#### Query Parameters
- `restaurant_id` (string, required): The ID of the restaurant.

#### Success Response (200 OK)
```json
{
  "conversation_id": "01a03c12-0f10-79cc-ae4f-6f32ca7a29b0",
  "history": [
    {
      "id": "abc-123",
      "role": "user",
      "content": "Food for 4",
      "createdAt": "2026-08-28T10:00:00Z"
    }
  ],
  "current_cart": [
    {
      "id": "01a03c12-0f10-79cc-ae4f-6f32ca7a29c1",
      "name": "Grilled Salmon",
      "category": "Main Course",
      "quantity": 2,
      "subtotal": 2400
    }
  ],
  "current_constraints": {
    "people_count": 4,
    "max_budget": null
  }
}
```
*Note: If no active conversation exists, `conversation_id` will be `null`.*

---

## 2. Restaurant & Menu Browsing

### `GET /api/restaurants`
Retrieves a list of all active restaurants available on the platform.

#### Success Response (200 OK)
```json
[
  {
    "id": "01a03c12-0f10-79cc-ae4f-6f32ca7a29b8",
    "name": "The Spice Garden",
    "cuisine_type": "Indian Fusion",
    "image_url": "https://images.unsplash.com/...",
    "is_active": true
  }
]
```

### `GET /api/restaurants/{id}/menu`
Retrieves available menu items for a specific restaurant, with allergens derived from their ingredients.

*Note: Responses are accelerated by an in-memory L1 cache (`MENU_CACHE`) with a 300-second TTL (`MENU_CACHE_TTL_SECONDS = 300.0` defined in `app.constants`), preventing repeated multi-table relational joins across ingredients and allergens.*

#### Success Response (200 OK)
```json
[
  {
    "id": "01a03c12-0f10-79cc-ae4f-6f32ca7a29c2",
    "name": "Paneer Tikka",
    "description": "Cottage cheese marinated in spices.",
    "price": 1450.0,
    "category": "Starter",
    "dietary_preference": "Vegetarian",
    "spice_level": "Medium",
    "servings": 5,
    "rating": 4.8
  }
]
```

---

## 3. Error Handling Specifications
The API uses standard HTTP status codes:
- **`200 OK`**: Successful processing (including graceful "Infeasible" ILP results, since the request itself was technically valid).
- **`400 Bad Request`**: Malformed JSON payloads or missing required fields.
- **`401 Unauthorized`**: Missing or invalid JWT tokens (for Admin endpoints).
- **`404 Not Found`**: The specified `restaurant_id` or `conversation_id` does not exist in the database.
- **`500 Internal Server Error`**: Catastrophic failure in the LLM connection, database asyncpg driver, or PuLP solver process.

### Deployment troubleshooting
- `OPTIONS ... 400`: the browser origin is not allowed by `CORS_ORIGINS` or `CORS_ORIGIN_REGEX`.
- `OPTIONS ... 200` followed by registration `500` with a bcrypt traceback: redeploy with `bcrypt==4.0.1`.
- `GET /api/restaurants` returns `[]`: seed the same production database referenced by `DATABASE_URL` using `cd /app && python -m seed.seed_data` in Render Shell.

---

## 4. Admin API & Compliance

### `GET /api/admin/audit-logs/{conversation_id}`
Securely retrieves the WORM (Write Once, Read Many) compliance log from Google Cloud Storage for a specific conversation.

#### Authentication
Requires a valid JWT token (`Authorization: Bearer <token>`). The user must have the `PLATFORM_ADMIN` or `RESTAURANT_ADMIN` role. If `RESTAURANT_ADMIN`, they must belong to the restaurant associated with the conversation.

#### Success Response (200 OK)
```json
{
  "log_file": "audit_log_01a03c12-0f10-79cc-ae4f-6f32ca7a29b0.json",
  "content": {
    "conversation_id": "01a03c12-0f10-79cc-ae4f-6f32ca7a29b0",
    "timestamp": "2026-08-28T10:00:00Z",
    "user_input": "Food for 5 people, 2 veg, low spice",
    "extracted_constraints": {
      "people_count": 5,
      "vegetarian_count": 2,
      "max_budget": null,
      "max_spice_level": "Low"
    },
    "mathematical_solver_output": {
      "status": "Optimal",
      "items": [ ... ]
    },
    "llm_explanation": "Here is a safe, optimal feast..."
  }
}
```

#### Error Responses
- **`401 Unauthorized`**: Missing or invalid token.
- **`403 Forbidden`**: The admin does not have permission to view logs for this restaurant.
- **`404 Not Found`**: The audit log has not been generated yet, or the conversation ID is invalid.
- **`500 Internal Server Error`**: Catastrophic failure in the GCS client or bucket access.

---

### `GET /api/admin/metrics`
Aggregates high-level KPI business metrics for the specified time range, computing current values and percentage growth compared to the preceding equivalent period.

#### Query Parameters
- `time_range` (string, optional, default: `"30d"`): Supported values are `"12h"`, `"24h"`, `"today"`, `"7d"`, `"30d"`, `"90d"`, `"all"`, and `"custom"`.
- `start_date` (string, optional, e.g. `"2026-09-01"`): Start date bound when `time_range="custom"`.
- `end_date` (string, optional, e.g. `"2026-09-15"`): End date bound when `time_range="custom"`.

#### Success Response (200 OK)
```json
{
  "total_orders": 42,
  "total_revenue": 58400.0,
  "avg_order_value": 1390.48,
  "total_conversations": 65,
  "time_range": "30d",
  "revenue_growth_pct": 14.5,
  "orders_growth_pct": 10.5,
  "conversations_growth_pct": 8.3
}
```

---

### `GET /api/admin/analytics`
Deep operational and business analytics suite including continuous zero-filled revenue and order trends, dish volume leaderboards with restaurant venue attribution, category distributions, solver feasibility health, and floor order logs.

#### Query Parameters
- `time_range` (string, optional, default: `"30d"`): Supported values: `"12h"`, `"24h"`, `"today"`, `"7d"`, `"30d"`, `"90d"`, `"all"`, `"custom"`.
- `start_date` (string, optional, e.g. `"2026-09-01"`): Start date bound when `time_range="custom"`.
- `end_date` (string, optional, e.g. `"2026-09-15"`): End date bound when `time_range="custom"`.

#### Success Response (200 OK)
```json
{
  "time_range": "30d",
  "total_revenue": 58400.0,
  "total_orders": 42,
  "avg_order_value": 1390.48,
  "active_conversations": 65,
  "revenue_growth_pct": 14.5,
  "orders_growth_pct": 10.5,
  "conversations_growth_pct": 8.3,
  "daily_trends": [
    { "date": "2026-09-01", "revenue": 3400.0, "orders": 3 }
  ],
  "top_dishes": [
    { 
      "name": "Butter Chicken", 
      "restaurant_name": "Spice Garden",
      "category": "Main Course", 
      "quantity_sold": 28, 
      "revenue": 12600.0 
    }
  ],
  "category_distribution": [
    { "category": "Main Course", "quantity_sold": 45, "revenue": 21000.0, "percentage": 48.5 }
  ],
  "solver_health": {
    "total_solves": 85,
    "optimal_count": 82,
    "infeasible_count": 3,
    "feasibility_rate_pct": 96.5,
    "avg_solve_time_ms": 12.4
  },
  "allergen_frequency": {
    "Peanuts": 18,
    "Dairy": 12
  },
  "recent_orders": [
    {
      "id": "01a09420-...",
      "restaurant_name": "Spice Garden",
      "total_amount": 1650.0,
      "status": "COMPLETED",
      "created_at": "2026-09-12T14:30:00Z",
      "items_count": 3
    }
  ]
}
```

---

### `POST /api/admin/insights/chat`
Conversational Executive Business Intelligence endpoint. Synthesizes answers from PostgreSQL database metrics and GCS WORM audit logs with role-based access control.

#### Request Body
```json
{
  "message": "What were our top 3 highest revenue dishes and what are the most common allergen requests?"
}
```

#### Success Response (200 OK)
```json
{
  "answer": "Based on PostgreSQL sales data, your top 3 revenue dishes are Butter Chicken (₹14,200), Paneer Tikka (₹8,700), and Dal Makhani (₹6,400). According to historical GCS audit logs, the most frequent allergen requests are Peanuts followed by Dairy.",
  "target_source": "BOTH",
  "data_sources": [
    "PostgreSQL Database",
    "GCS WORM Audit Logs"
  ],
  "metrics_summary": {
    "orders": { "total_orders": 42, "total_revenue": "₹58,400.00" },
    "gcs_records": 85,
    "total_tokens": 124000
  }
}
```

---

### `POST /api/admin/insights/chat/stream`
Server-Sent Events streaming endpoint for conversational business intelligence. Streams classification status, data retrieval updates, token-by-token insight answer from Gemini 3.5 Flash Lite, and completion frames.

#### Media Type
`text/event-stream`

#### Event Types
1. **`event: status`**: Dispatched during query classification and data querying stages.
2. **`event: metadata`**: Dispatches target sources (`POSTGRES`, `GCS`, `BOTH`) and metrics summary.
3. **`event: token`**: Incremental natural-language executive answer chunk.
4. **`event: done`**: Dispatched upon completion with the full synthesized answer and metadata.



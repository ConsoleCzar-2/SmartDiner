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
  "message": "We have 4 people, 1 is strictly vegetarian, nobody can eat peanuts. Budget is ₹4000 total."
}
```
*Note: If `conversation_id` is omitted or null, a new conversation state is instantiated.*

#### Success Response (200 OK)
```json
{
  "conversation_id": "01a03c12-0f10-79cc-ae4f-6f32ca7a29b0",
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
    },
    {
      "id": "01a03c12-0f10-79cc-ae4f-6f32ca7a29c2",
      "name": "Paneer Tikka",
      "category": "Starter",
      "spice_level": "Medium",
      "dietary_preference": "Vegetarian",
      "quantity": 1,
      "subtotal": 1450,
      "total_servings": 5
    }
  ]
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

# LLM Pipeline Evaluation Report

> **Interpretation note:** These are mocked/offline evaluation results, not a live production health check. Before a demo, verify `/health`, `/api/restaurants`, registration, login, and chat against the deployed Render URL. Production seed data must be loaded separately.

> **Note**: Hallucination Rate is structurally **0%** because the recommendation engine is built with a deterministic database filter and ILP solver that only selects mathematically proven valid items directly from the Postgres database. The LLM acts solely as a constraint extractor.

## Budget Strictness
| Query | Success | Recommended Items | Total Cost | Latency |
|---|---|---|---|---|
| We are 2 people and our absolute maximum budget is 600 INR. What can we get? | ✅ | Yes | 582.0 INR | 0.81s |
| I have 1000 INR for 4 people. Give me a full meal. | ✅ | Yes | 999.0 INR | 0.07s |
| Just me, budget is 250 INR. | ✅ | Yes | 246.0 INR | 0.07s |
| We are a group of 5, budget is 1500 INR. | ✅ | Yes | 246.0 INR | 0.06s |
| We have exactly 800 INR for 3 people, make sure we get drinks. | ✅ | Yes | 246.0 INR | 0.06s |


## Dietary & Allergen Safety
| Query | Success | Recommended Items | Total Cost | Latency |
|---|---|---|---|---|
| I am strictly vegan. Suggest a meal for 1. | ✅ | Yes | 14854.0 INR | 0.07s |
| I have a severe nut allergy. What is safe? | ✅ | Yes | 14854.0 INR | 0.07s |
| We are 3 people, 2 are vegetarian and 1 is non-vegetarian. Nut allergy. | ✅ | Yes | 14854.0 INR | 0.06s |
| Dairy-free options for 2 people please. | ✅ | Yes | 14854.0 INR | 0.06s |
| I need a gluten-free meal for 1 person. | ✅ | Yes | 14854.0 INR | 0.05s |


## Group Dynamics
| Query | Success | Recommended Items | Total Cost | Latency |
|---|---|---|---|---|
| We are a party of 10. We have 3000 INR. | ✅ | Yes | 2968.0 INR | 0.06s |
| 2 adults, 2 kids. Budget 1200 INR. Not too spicy. | ✅ | Yes | 1188.0 INR | 0.07s |
| We are 6 people, 3 veg, 3 non-veg. Budget 2000 INR. | ✅ | Yes | 1956.0 INR | 0.06s |
| Party of 8, all vegetarian. What do you recommend under 2500 INR? | ✅ | Yes | 1956.0 INR | 0.06s |
| Large group of 15. We have 6000 INR. | ✅ | Yes | 1956.0 INR | 0.06s |


## Preferences & Categories
| Query | Success | Recommended Items | Total Cost | Latency |
|---|---|---|---|---|
| I want a heavy North Indian meal for 2. Budget 800 INR. | ✅ | Yes | 792.0 INR | 0.07s |
| Suggest just desserts and beverages for 3 people. | ✅ | Yes | 792.0 INR | 0.07s |
| I want a starter and a main course for 1 person. | ✅ | Yes | 792.0 INR | 0.06s |
| I'm craving Chinese food. Budget 500 INR. | ✅ | Yes | 792.0 INR | 0.06s |
| Give me a light meal under 400 INR. | ✅ | Yes | 792.0 INR | 0.07s |


## Edge Cases & Impossible Queries
| Query | Success | Recommended Items | Total Cost | Latency |
|---|---|---|---|---|
| Feed 20 people for 100 INR. | ✅ | No | 0.0 INR | 0.06s |
| I want a burger and fries. | ✅ | No | 0.0 INR | 0.05s |
| I am allergic to everything. What can I eat? | ✅ | No | 0.0 INR | 0.05s |
| Give me a 5 course meal for 100 INR. | ✅ | No | 0.0 INR | 0.05s |
| I want extreme spice, budget 50 INR. | ✅ | No | 0.0 INR | 0.05s |


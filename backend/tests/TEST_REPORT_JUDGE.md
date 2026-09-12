# SmartDiner LLM-as-Judge Qualitative Evaluation Report

## Overall Benchmark Scores
- **Average Extraction Quality Score:** 9.0 / 10.0
- **Allergen & Dietary Safety Compliance:** 87.5%
- **Evaluator Model:** Gemini 3.5 Flash Lite (temperature 0.0)
- **Cases Evaluated:** 8 cross-category benchmark queries

## Case-by-Case Evaluation Matrix
| ID | Category | Score (/10) | Safety Check | Judge Critique |
|---|---|---|---|---|
| tc_01 | Basic Group & Budget | 10.0 | SAFE | The extracted output perfectly captures the required people count (4) and the maximum budget (2000.0 INR) from the user message, while appropriately setting default/null values for unmentioned constraints without introducing any errors or violating safety. |
| tc_06 | Dietary Split | 6.0 | SAFE | The extraction successfully identified the total party count, vegetarian count, and budget, but completely missed extracting the non_vegetarian_count, leaving it as null despite it being explicitly stated in the user message. |
| tc_11 | Allergens | 10.0 | SAFE | The extracted output perfectly captures all essential constraints from the user message, including the correct party size (3), the budget (1500.0), and crucially, the severe peanut allergy in the excluded allergens list. Additional schema fields are appropriately defaulted. |
| tc_16 | Spice Preference | 10.0 | SAFE | The extracted output perfectly captures all constraints from the user message, including party size, budget, and the non-spicy requirement, matching the ground truth accurately while properly formatting optional fields. |
| tc_21 | Dish Mentions & Exclusions | 10.0 | SAFE | The extracted output perfectly captures all constraints from the user message, including party size (4), budget (2000), and the specific dish request (chicken biryani). All additional schema fields are appropriately defaulted. |
| tc_26 | Colloquial Quantities | 10.0 | SAFE | The extraction perfectly captured the people count (2, derived from 'Me and my girlfriend') and the maximum budget (1000.0). All optional fields are appropriately defaulted and no constraints were missed. |
| tc_36 | Complex Multi-Constraint | 6.0 | UNSAFE | The extracted output correctly captured the total people count, budget, vegan count, and dairy allergen, but critically failed to capture the non-vegetarian count (setting it to null) despite it being explicitly stated in the user message. |
| tc_46 | Colloquial Numbers | 10.0 | SAFE | The extracted output perfectly captures the party size (12) and the maximum budget (6000 INR) as specified in the user message, while appropriately setting default/null values for unspecified optional fields. |

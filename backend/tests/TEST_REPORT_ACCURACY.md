# SmartDiner LLM Constraint Extraction — Golden Test Suite Accuracy Report

## Summary Metrics
- **Total Golden Test Cases:** 15
- **Passed Cases:** 15
- **Failed Cases:** 0
- **Overall Extraction Accuracy:** 100.0%
- **Pass Threshold:** 85.0%
- **Status:** PASSED

## Accuracy Breakdown by Category
| Category | Cases | Passed | Accuracy (%) |
|---|---|---|---|
| Allergens | 1 | 1 | 100.0% |
| Basic Group & Budget | 2 | 2 | 100.0% |
| Colloquial Numbers | 1 | 1 | 100.0% |
| Colloquial Quantities | 1 | 1 | 100.0% |
| Complex Multi-Constraint | 1 | 1 | 100.0% |
| Cuisine Preferences | 1 | 1 | 100.0% |
| Currency variations | 1 | 1 | 100.0% |
| Dietary Keywords | 1 | 1 | 100.0% |
| Dietary Split | 1 | 1 | 100.0% |
| Dish Mentions & Exclusions | 2 | 2 | 100.0% |
| Edge Cases | 1 | 1 | 100.0% |
| Multiple Allergens | 1 | 1 | 100.0% |
| Spice Preference | 1 | 1 | 100.0% |

## Detailed Case Results
| ID | Category | Status | Input Message | Failure Details |
|---|---|---|---|---|
| tc_01 | Basic Group & Budget | PASS | Order food for 4 people with a budget of 2000 INR. | - |
| tc_05 | Basic Group & Budget | PASS | Party of 10, total budget is 5000. | - |
| tc_09 | Dietary Split | PASS | Strictly non-veg dinner for 2 people, budget 1200. | - |
| tc_13 | Allergens | PASS | 2 people, budget 1000. No gluten and no nuts. | - |
| tc_17 | Spice Preference | PASS | Food for 4, budget 2000. Mild spice only. | - |
| tc_21 | Dish Mentions & Exclusions | PASS | Order for 4 people under 2000. Must include chicken biryani. | - |
| tc_25 | Dish Mentions & Exclusions | PASS | Feed 3 people under 1500 with dal makhani, but no rice. | - |
| tc_29 | Colloquial Quantities | PASS | Myself and 3 colleagues, budget 2000 total. | - |
| tc_33 | Cuisine Preferences | PASS | Italian dinner for 2, budget 1400. | - |
| tc_37 | Complex Multi-Constraint | PASS | Table of 6, budget 3600. All veg, Jain food only (no onions/garlic), mild spice. | - |
| tc_41 | Edge Cases | PASS | Can you order something light for 1 person? | - |
| tc_44 | Dietary Keywords | PASS | Halal chicken dinner for 4 people, budget 2000. | - |
| tc_47 | Colloquial Numbers | PASS | Half a dozen guests, budget 3000. | - |
| tc_49 | Currency variations | PASS | 3 people, ₹1800 budget, 1 veg 2 non-veg. | - |
| tc_50 | Multiple Allergens | PASS | Food for 4, budget 2200. Highly allergic to gluten, soy, and peanuts. | - |

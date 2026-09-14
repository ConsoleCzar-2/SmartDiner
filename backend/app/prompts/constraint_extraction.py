CONSTRAINT_EXTRACTION_SYSTEM_PROMPT = """Extract dietary and food ordering constraints from user messages into strict JSON.

STATE MERGING:
If Existing Constraints are provided, output ONLY the DELTA (fields changed in this message). Leave unmentioned fields null/empty.
- New order: output absolute values, `is_modification`: false.
- Ongoing order modification: set `is_modification`: true.

RULES:
1. spice: default "Any" for new orders unless mild/low/high/extreme specified.
2. allergens: Peanuts, Tree Nuts, Dairy, Gluten, Soy, Shellfish, Eggs, Sesame, Fish.
3. people_count: minimum 1 for new orders ("couple" -> 2).
4. budget: numeric value in INR; terms like "cheap" or "affordable" -> leave null.
5. "vegan" sets vegan_count, NOT vegetarian_count.
6. non_vegetarian_count: set if explicitly stated, else null (auto-computed).
7. QUANTITIES:
   - Category minimum counts ("2 breads and 2 drinks") -> populate `category_min_counts` and `preferred_categories`.
   - Specific dish counts ("2 garlic naans") -> populate `dish_quantities` and `specific_dish_requests`.
8. CART CONTEXT:
   - Remove dish -> add to `excluded_dishes`.
   - Swap/replace -> add old dish to `excluded_dishes`, new item/category to `preferred_categories`/`specific_dish_requests`.

EXAMPLES:
User: "We are 3 friends, one is vegetarian. Make it spicy. Budget around 1500."
Existing: {}
JSON: {"people_count": 3, "vegetarian_count": 1, "vegan_count": 0, "max_budget": 1500.0, "max_spice_level": "High", "is_modification": false}

User: "increase bread, beverage and dessert to 2 each. Also add another starter."
Existing: {"people_count": 2, "max_budget": 2000.0, "preferred_categories": ["Starter", "Main Course"]}
JSON: {"preferred_categories": ["Bread", "Beverage", "Dessert", "Starter", "Main Course"], "category_min_counts": {"Bread": 2, "Beverage": 2, "Dessert": 2, "Starter": 2}, "is_modification": true}

User: "Actually, make it 2 garlic naans and 2 masala chais."
Existing: {"people_count": 2, "max_budget": 2000.0}
Cart: [{"name": "Garlic Naan", "category": "Bread"}, {"name": "Masala Kadak Chai", "category": "Beverage"}]
JSON: {"preferred_categories": ["Bread", "Beverage"], "category_min_counts": {"Bread": 2, "Beverage": 2}, "specific_dish_requests": ["Garlic Naan", "Masala Kadak Chai"], "dish_quantities": {"Garlic Naan": 2, "Masala Kadak Chai": 2}, "is_modification": true}

User: "Remove Paneer Tikka and add a beverage instead."
Existing: {"people_count": 4}
Cart: [{"name": "Spice Paneer Tikka 5"}, {"name": "Chicken Biryani"}]
JSON: {"preferred_categories": ["Beverage"], "excluded_dishes": ["Spice Paneer Tikka 5"], "is_modification": true}

User: "We are a couple, both vegan. Keep it under 800."
Existing: {}
JSON: {"people_count": 2, "vegetarian_count": 0, "vegan_count": 2, "max_budget": 800.0, "max_spice_level": "Any", "is_modification": false}
"""



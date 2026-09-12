"""Centralized system constants for SmartDiner backend."""

# -----------------------------------------------------------------------------
# Cache TTL Configurations (in seconds)
# -----------------------------------------------------------------------------
# In-memory cache TTL for full restaurant menu browsing (GET /api/restaurants/{id}/menu)
MENU_CACHE_TTL_SECONDS: float = 300.0  # 5 minutes

# In-memory cache TTL for filtered menu query execution in the AI recommendation pipeline
MENU_FILTER_CACHE_TTL_SECONDS: float = 300.0  # 5 minutes (kept in sync with full menu cache)

# -----------------------------------------------------------------------------
# Platform Currency
# -----------------------------------------------------------------------------
PLATFORM_CURRENCY_CODE: str = "INR"
PLATFORM_CURRENCY_SYMBOL: str = "₹"

# -----------------------------------------------------------------------------
# Standard Food & Dining Taxonomy
# -----------------------------------------------------------------------------
SUPPORTED_ALLERGENS: list[str] = [
    "Peanuts",
    "Tree Nuts",
    "Dairy",
    "Gluten",
    "Soy",
    "Shellfish",
    "Eggs",
    "Sesame",
    "Fish",
]

SPICE_ORDER: dict[str, int] = {
    "None": 0,
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Extreme": 4,
}

CUISINE_SYNONYMS: dict[str, str] = {
    "mughlai": "North Indian",
    "punjabi": "North Indian",
    "tandoori": "North Indian",
    "indian": "North Indian",
    "north indian": "North Indian",
    "south indian": "South Indian",
    "chettinad": "South Indian",
    "kerala": "South Indian",
    "chinese": "Chinese",
    "indo-chinese": "Indo-Chinese",
    "cantonese": "Chinese",
    "sichuan": "Chinese",
    "szechuan": "Chinese",
    "asian": "Chinese",
    "italian": "Italian",
    "continental": "Continental",
    "european": "Continental",
    "mediterranean": "Continental",
    "fast food": "Fast Food",
    "american": "American",
    "japanese": "Other",
    "pan-asian": "Other",
    "other": "Other",
}

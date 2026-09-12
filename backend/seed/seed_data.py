import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem
from app.models.allergen import Allergen
from app.models.ingredient import Ingredient, MenuItemIngredient, IngredientAllergen
from app.models.dietary_tag import DietaryTag, MenuItemTag
from app.models.admin_user import AdminUser
from app.services.auth import get_password_hash
from app.database import AsyncSessionLocal

CATEGORY_IMAGES = {
    "Starter": "https://images.unsplash.com/photo-1541529086526-db283c563270?w=500&q=80",
    "Main Course": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500&q=80",
    "Bread": "https://images.unsplash.com/photo-1601050690597-df0568a70950?w=500&q=80",
    "Rice": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?w=500&q=80",
    "Beverage": "https://images.unsplash.com/photo-1544145945-f90425340c7e?w=500&q=80",
    "Dessert": "https://images.unsplash.com/photo-1551024601-bec78aea704b?w=500&q=80",
    "Side": "https://images.unsplash.com/photo-1628294895950-9805252327bc?w=500&q=80",
}

async def seed(session_factory=None):
    factory = session_factory or AsyncSessionLocal
    async with factory() as session:
        # Check if we already have data
        result = await session.execute(select(Restaurant).limit(1))
        if result.scalar_one_or_none():
            print("Database already has data. Run truncate_db first if you want a fresh start. Exiting.")
            return

        print("Starting comprehensive realistic seed (6 restaurants with curated diverse menus)...")

        # 1. Create 6 Diverse Restaurants matching DB check constraint:
        # ('North Indian', 'South Indian', 'Chinese', 'Indo-Chinese', 'Italian', 'Continental', 'Fast Food', 'American', 'Beverages', 'Desserts', 'Other')
        restaurants_data = [
            {
                "name": "Spice Garden",
                "description": "Authentic North Indian fine dining with royal Mughlai gravies, clay-oven tandoori grills, and fragrant slow-cooked biryanis.",
                "address": "123 Curry Lane, Connaught Place",
                "cuisine_type": "North Indian",
                "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500&q=80"
            },
            {
                "name": "Dragon's Wok",
                "description": "Fiery wok-tossed delights, handcrafted Cantonese dim sums, and vibrant Sichuan noodles bursting with umami flavors.",
                "address": "456 Silk Road, Chinatown",
                "cuisine_type": "Chinese",
                "image_url": "https://images.unsplash.com/photo-1552566626-52f8b828add9?w=500&q=80"
            },
            {
                "name": "The Grand Kitchen",
                "description": "European bistro elegance featuring artisan hand-stretched wood-fired pizzas, slow-simmered pastas, and Mediterranean cuts.",
                "address": "789 Main Boulevard, Park Avenue",
                "cuisine_type": "Italian",
                "image_url": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=500&q=80"
            },
            {
                "name": "South Spice Heritage",
                "description": "Traditional South Indian culinary heritage featuring crispy fermented dosas, steamed idlis, Chettinad curries, and degree filter coffee.",
                "address": "101 Temple Road, Mylapore",
                "cuisine_type": "South Indian",
                "image_url": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500&q=80"
            },
            {
                "name": "Tokyo Umami",
                "description": "Traditional East Asian dining showcasing rich tonkotsu broths, ramen noodles, fresh nigiri platters, and ceremonial matcha.",
                "address": "202 Sakura Way, Downtown",
                "cuisine_type": "Other",
                "image_url": "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=500&q=80"
            },
            {
                "name": "Green Haven Cafe",
                "description": "Plant-forward sanctuary crafting wholesome vegan bowls, organic avocado toast, artisan cheeses, and fresh vegetarian & vegan fare.",
                "address": "303 Botanical Square, Green Zone",
                "cuisine_type": "Continental",
                "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500&q=80"
            }
        ]

        restaurants = []
        for rd in restaurants_data:
            r = Restaurant(**rd)
            session.add(r)
            restaurants.append(r)

        await session.commit()
        for r in restaurants:
            await session.refresh(r)

        # 2. Create Allergens
        allergen_names = ["Peanuts", "Tree Nuts", "Dairy", "Gluten", "Soy", "Shellfish", "Eggs", "Sesame", "Fish", "Mustard"]
        allergens = {}
        for name in allergen_names:
            a = Allergen(name=name)
            session.add(a)
            allergens[name] = a
        await session.commit()

        # 3. Create Dietary Tags
        tag_names = ["Vegetarian", "Vegan", "Jain", "Eggetarian", "Non-Vegetarian", "Keto", "Halal"]
        tags = {}
        for name in tag_names:
            t = DietaryTag(name=name)
            session.add(t)
            tags[name] = t
        await session.commit()

        # 4. Create Ingredients & map to allergens
        ingredients_data = {
            "Chicken": [], "Paneer": ["Dairy"], "Milk": ["Dairy"], "Butter": ["Dairy"], "Cheese": ["Dairy"],
            "Flour": ["Gluten"], "Rice": [], "Eggs": ["Eggs"], "Peanut Butter": ["Peanuts"],
            "Soy Sauce": ["Soy", "Gluten"], "Tofu": ["Soy"], "Shrimp": ["Shellfish"], "Crab": ["Shellfish"],
            "Fish": ["Fish"], "Cashews": ["Tree Nuts"], "Almonds": ["Tree Nuts"], "Sesame Oil": ["Sesame"],
            "Onion": [], "Garlic": [], "Tomato": [], "Lentils": [], "Potato": [], "Mushroom": [], "Bell Pepper": [],
            "Sugar": [], "Tea Leaves": [], "Coffee Beans": [], "Olive Oil": [], "Basil": [], "Coconut": [],
            "Mustard Seeds": ["Mustard"], "Curry Leaves": [], "Lamb": [], "Beef": [], "Pork": [],
            "Avocado": [], "Corn": [], "Black Beans": [], "Matcha": [], "Seaweed": [], "Miso": ["Soy"]
        }
        ingredients = {}
        for name, algs in ingredients_data.items():
            ing = Ingredient(name=name)
            session.add(ing)
            await session.flush()
            ingredients[name] = ing
            for alg_name in algs:
                session.add(IngredientAllergen(ingredient_id=ing.id, allergen_id=allergens[alg_name].id))

        await session.commit()

        # 5. Distinct Curated Menus (18-22 items each, no duplicate names, rich diversity)
        
        # Menu 1: Spice Garden (North Indian)
        spice_menu = [
            # Starters
            {"name": "Paneer Tikka Skewers", "category": "Starter", "price": 280, "dietary": "Vegetarian", "spice": "Medium", "cuisine": "North Indian", "servings": 1, "ings": ["Paneer", "Bell Pepper", "Onion"], "tags": ["Vegetarian"]},
            {"name": "Tandoori Chicken Tikka", "category": "Starter", "price": 340, "dietary": "Non-Vegetarian", "spice": "High", "cuisine": "North Indian", "servings": 1, "ings": ["Chicken", "Mustard Seeds", "Onion"], "tags": ["Non-Vegetarian", "Halal"]},
            {"name": "Hara Bhara Kebab", "category": "Starter", "price": 240, "dietary": "Vegan", "spice": "Low", "cuisine": "North Indian", "servings": 1, "ings": ["Potato", "Lentils"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            {"name": "Amritsari Fish Fry", "category": "Starter", "price": 380, "dietary": "Non-Vegetarian", "spice": "High", "cuisine": "North Indian", "servings": 1, "ings": ["Fish", "Mustard Seeds", "Garlic"], "tags": ["Non-Vegetarian"]},
            # Mains
            {"name": "Dal Makhani", "category": "Main Course", "price": 270, "dietary": "Vegetarian", "spice": "Low", "cuisine": "North Indian", "servings": 2, "ings": ["Lentils", "Butter", "Tomato"], "tags": ["Vegetarian"]},
            {"name": "Butter Chicken Delhi Style", "category": "Main Course", "price": 420, "dietary": "Non-Vegetarian", "spice": "Medium", "cuisine": "North Indian", "servings": 2, "ings": ["Chicken", "Butter", "Tomato", "Cashews"], "tags": ["Non-Vegetarian", "Halal"]},
            {"name": "Palak Paneer", "category": "Main Course", "price": 310, "dietary": "Vegetarian", "spice": "Low", "cuisine": "North Indian", "servings": 2, "ings": ["Paneer", "Garlic", "Tomato"], "tags": ["Vegetarian"]},
            {"name": "Kashmiri Mutton Rogan Josh", "category": "Main Course", "price": 490, "dietary": "Non-Vegetarian", "spice": "High", "cuisine": "North Indian", "servings": 2, "ings": ["Lamb", "Onion", "Garlic"], "tags": ["Non-Vegetarian", "Halal"]},
            {"name": "Jain Paneer Lababdar", "category": "Main Course", "price": 320, "dietary": "Vegetarian", "spice": "Low", "cuisine": "North Indian", "servings": 2, "ings": ["Paneer", "Tomato", "Cashews"], "tags": ["Vegetarian", "Jain"]},
            {"name": "Yellow Dal Tadka", "category": "Main Course", "price": 220, "dietary": "Vegan", "spice": "Medium", "cuisine": "North Indian", "servings": 2, "ings": ["Lentils", "Tomato", "Garlic"], "tags": ["Vegetarian", "Vegan"]},
            # Breads
            {"name": "Butter Naan", "category": "Bread", "price": 60, "dietary": "Vegetarian", "spice": "None", "cuisine": "North Indian", "servings": 1, "ings": ["Flour", "Butter"], "tags": ["Vegetarian"]},
            {"name": "Garlic Naan", "category": "Bread", "price": 75, "dietary": "Vegetarian", "spice": "None", "cuisine": "North Indian", "servings": 1, "ings": ["Flour", "Butter", "Garlic"], "tags": ["Vegetarian"]},
            {"name": "Tandoori Roti", "category": "Bread", "price": 40, "dietary": "Vegan", "spice": "None", "cuisine": "North Indian", "servings": 1, "ings": ["Flour"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            # Rice
            {"name": "Hyderabadi Dum Biryani (Chicken)", "category": "Rice", "price": 440, "dietary": "Non-Vegetarian", "spice": "High", "cuisine": "North Indian", "servings": 2, "ings": ["Rice", "Chicken", "Onion", "Cashews"], "tags": ["Non-Vegetarian", "Halal"]},
            {"name": "Subz Dum Biryani", "category": "Rice", "price": 320, "dietary": "Vegetarian", "spice": "Medium", "cuisine": "North Indian", "servings": 2, "ings": ["Rice", "Paneer", "Onion", "Cashews"], "tags": ["Vegetarian"]},
            {"name": "Jeera Steamed Rice", "category": "Rice", "price": 160, "dietary": "Vegan", "spice": "None", "cuisine": "North Indian", "servings": 2, "ings": ["Rice"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            # Sides
            {"name": "Boondi Raita", "category": "Side", "price": 90, "dietary": "Vegetarian", "spice": "None", "cuisine": "North Indian", "servings": 1, "ings": ["Milk"], "tags": ["Vegetarian"]},
            # Beverages
            {"name": "Amritsari Sweet Lassi", "category": "Beverage", "price": 110, "dietary": "Vegetarian", "spice": "None", "cuisine": "North Indian", "servings": 1, "ings": ["Milk", "Sugar"], "tags": ["Vegetarian"]},
            {"name": "Masala Kadak Chai", "category": "Beverage", "price": 70, "dietary": "Vegetarian", "spice": "None", "cuisine": "North Indian", "servings": 1, "ings": ["Tea Leaves", "Milk", "Sugar"], "tags": ["Vegetarian"]},
            # Desserts
            {"name": "Warm Gulab Jamun (2 pcs)", "category": "Dessert", "price": 140, "dietary": "Vegetarian", "spice": "None", "cuisine": "North Indian", "servings": 1, "ings": ["Flour", "Milk", "Sugar"], "tags": ["Vegetarian"]},
            {"name": "Kesar Rasmalai", "category": "Dessert", "price": 180, "dietary": "Vegetarian", "spice": "None", "cuisine": "North Indian", "servings": 1, "ings": ["Paneer", "Milk", "Sugar", "Almonds"], "tags": ["Vegetarian"]}
        ]

        # Menu 2: Dragon's Wok (Chinese / Indo-Chinese)
        dragon_menu = [
            # Starters
            {"name": "Crispy Veg Spring Rolls", "category": "Starter", "price": 220, "dietary": "Vegan", "spice": "Low", "cuisine": "Chinese", "servings": 1, "ings": ["Flour", "Onion", "Tomato"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Chicken Dim Sum Basket", "category": "Starter", "price": 310, "dietary": "Non-Vegetarian", "spice": "Low", "cuisine": "Chinese", "servings": 1, "ings": ["Chicken", "Flour", "Garlic", "Soy Sauce"], "tags": ["Non-Vegetarian", "Halal"]},
            {"name": "Fiery Dragon Chicken", "category": "Starter", "price": 330, "dietary": "Non-Vegetarian", "spice": "Extreme", "cuisine": "Chinese", "servings": 1, "ings": ["Chicken", "Soy Sauce", "Garlic"], "tags": ["Non-Vegetarian"]},
            {"name": "Crispy Chilli Paneer", "category": "Starter", "price": 270, "dietary": "Vegetarian", "spice": "High", "cuisine": "Indo-Chinese", "servings": 1, "ings": ["Paneer", "Soy Sauce", "Bell Pepper"], "tags": ["Vegetarian"]},
            {"name": "Golden Prawn Crackers", "category": "Starter", "price": 160, "dietary": "Non-Vegetarian", "spice": "None", "cuisine": "Chinese", "servings": 1, "ings": ["Shrimp", "Flour"], "tags": ["Non-Vegetarian"]},
            # Mains
            {"name": "Kung Pao Chicken", "category": "Main Course", "price": 360, "dietary": "Non-Vegetarian", "spice": "High", "cuisine": "Chinese", "servings": 2, "ings": ["Chicken", "Soy Sauce", "Peanut Butter"], "tags": ["Non-Vegetarian"]},
            {"name": "Sichuan Mapo Tofu", "category": "Main Course", "price": 300, "dietary": "Vegetarian", "spice": "Extreme", "cuisine": "Chinese", "servings": 2, "ings": ["Tofu", "Soy Sauce", "Garlic", "Sesame Oil"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Sweet and Sour Crispy Pork", "category": "Main Course", "price": 410, "dietary": "Non-Vegetarian", "spice": "Medium", "cuisine": "Chinese", "servings": 2, "ings": ["Pork", "Sugar", "Bell Pepper"], "tags": ["Non-Vegetarian"]},
            {"name": "Veg Hakka Noodles", "category": "Main Course", "price": 240, "dietary": "Vegan", "spice": "Low", "cuisine": "Indo-Chinese", "servings": 2, "ings": ["Flour", "Soy Sauce", "Bell Pepper"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Shrimp Chow Mein", "category": "Main Course", "price": 390, "dietary": "Non-Vegetarian", "spice": "Medium", "cuisine": "Chinese", "servings": 2, "ings": ["Shrimp", "Flour", "Soy Sauce"], "tags": ["Non-Vegetarian"]},
            # Rice
            {"name": "Wok Fried Egg Rice", "category": "Rice", "price": 230, "dietary": "Non-Vegetarian", "spice": "Low", "cuisine": "Chinese", "servings": 2, "ings": ["Rice", "Eggs", "Soy Sauce", "Onion"], "tags": ["Eggetarian"]},
            {"name": "Smoked Chicken Fried Rice", "category": "Rice", "price": 290, "dietary": "Non-Vegetarian", "spice": "Medium", "cuisine": "Chinese", "servings": 2, "ings": ["Rice", "Chicken", "Soy Sauce"], "tags": ["Non-Vegetarian"]},
            {"name": "Fragrant Jasmine Rice", "category": "Rice", "price": 150, "dietary": "Vegan", "spice": "None", "cuisine": "Chinese", "servings": 2, "ings": ["Rice"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            # Sides
            {"name": "Sesame Wok Greens", "category": "Side", "price": 180, "dietary": "Vegan", "spice": "Low", "cuisine": "Chinese", "servings": 1, "ings": ["Garlic", "Sesame Oil"], "tags": ["Vegetarian", "Vegan"]},
            # Beverages
            {"name": "Classic Boba Milk Tea", "category": "Beverage", "price": 190, "dietary": "Vegetarian", "spice": "None", "cuisine": "Chinese", "servings": 1, "ings": ["Tea Leaves", "Milk", "Sugar"], "tags": ["Vegetarian"]},
            {"name": "Hot Jasmine Blossom Tea", "category": "Beverage", "price": 130, "dietary": "Vegan", "spice": "None", "cuisine": "Chinese", "servings": 1, "ings": ["Tea Leaves"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            # Desserts
            {"name": "Crispy Fried Ice Cream", "category": "Dessert", "price": 210, "dietary": "Vegetarian", "spice": "None", "cuisine": "Chinese", "servings": 1, "ings": ["Milk", "Flour", "Sugar"], "tags": ["Vegetarian"]},
            {"name": "Mango Sticky Coconut Rice", "category": "Dessert", "price": 240, "dietary": "Vegan", "spice": "None", "cuisine": "Chinese", "servings": 1, "ings": ["Rice", "Coconut", "Sugar"], "tags": ["Vegetarian", "Vegan"]}
        ]

        # Menu 3: The Grand Kitchen (Italian / Continental)
        grand_menu = [
            # Starters
            {"name": "Tuscan Tomato Bruschetta", "category": "Starter", "price": 230, "dietary": "Vegan", "spice": "Low", "cuisine": "Italian", "servings": 1, "ings": ["Flour", "Tomato", "Garlic", "Olive Oil", "Basil"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Classic Caesar Salad", "category": "Starter", "price": 260, "dietary": "Vegetarian", "spice": "None", "cuisine": "Continental", "servings": 1, "ings": ["Cheese", "Olive Oil", "Garlic"], "tags": ["Vegetarian", "Keto"]},
            {"name": "Charred Chicken Caesar Salad", "category": "Starter", "price": 330, "dietary": "Non-Vegetarian", "spice": "None", "cuisine": "Continental", "servings": 1, "ings": ["Chicken", "Cheese", "Olive Oil", "Garlic"], "tags": ["Non-Vegetarian", "Keto"]},
            # Mains
            {"name": "Wood-fired Margherita Pizza", "category": "Main Course", "price": 460, "dietary": "Vegetarian", "spice": "None", "cuisine": "Italian", "servings": 2, "ings": ["Flour", "Tomato", "Cheese", "Olive Oil", "Basil"], "tags": ["Vegetarian"]},
            {"name": "Rustic Pepperoni Pizza", "category": "Main Course", "price": 580, "dietary": "Non-Vegetarian", "spice": "Medium", "cuisine": "Italian", "servings": 2, "ings": ["Flour", "Tomato", "Cheese", "Beef"], "tags": ["Non-Vegetarian"]},
            {"name": "Slow-Simmered Spaghetti Bolognese", "category": "Main Course", "price": 440, "dietary": "Non-Vegetarian", "spice": "Low", "cuisine": "Italian", "servings": 1, "ings": ["Flour", "Tomato", "Beef", "Garlic", "Olive Oil"], "tags": ["Non-Vegetarian"]},
            {"name": "Penne all'Arrabbiata", "category": "Main Course", "price": 370, "dietary": "Vegan", "spice": "High", "cuisine": "Italian", "servings": 1, "ings": ["Flour", "Tomato", "Garlic", "Olive Oil", "Basil"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Creamy Wild Mushroom Risotto", "category": "Main Course", "price": 470, "dietary": "Vegetarian", "spice": "Low", "cuisine": "Italian", "servings": 1, "ings": ["Rice", "Mushroom", "Cheese", "Butter"], "tags": ["Vegetarian"]},
            {"name": "Pan-Seared Atlantic Salmon", "category": "Main Course", "price": 760, "dietary": "Non-Vegetarian", "spice": "Low", "cuisine": "Continental", "servings": 1, "ings": ["Fish", "Olive Oil", "Garlic"], "tags": ["Non-Vegetarian", "Keto"]},
            {"name": "Grilled Tenderloin Steak", "category": "Main Course", "price": 860, "dietary": "Non-Vegetarian", "spice": "Medium", "cuisine": "Continental", "servings": 1, "ings": ["Beef", "Olive Oil", "Garlic", "Butter"], "tags": ["Non-Vegetarian", "Keto"]},
            # Breads & Sides
            {"name": "Parmesan Garlic Bread", "category": "Bread", "price": 180, "dietary": "Vegetarian", "spice": "None", "cuisine": "Italian", "servings": 1, "ings": ["Flour", "Garlic", "Butter", "Cheese"], "tags": ["Vegetarian"]},
            {"name": "Truffle Parmesan Fries", "category": "Side", "price": 190, "dietary": "Vegetarian", "spice": "None", "cuisine": "Continental", "servings": 1, "ings": ["Potato", "Cheese", "Olive Oil"], "tags": ["Vegetarian"]},
            # Beverages
            {"name": "Single Origin Espresso", "category": "Beverage", "price": 120, "dietary": "Vegan", "spice": "None", "cuisine": "Italian", "servings": 1, "ings": ["Coffee Beans"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            {"name": "Velvet Cappuccino", "category": "Beverage", "price": 170, "dietary": "Vegetarian", "spice": "None", "cuisine": "Italian", "servings": 1, "ings": ["Coffee Beans", "Milk", "Sugar"], "tags": ["Vegetarian"]},
            {"name": "Fresh Lemon Iced Tea", "category": "Beverage", "price": 140, "dietary": "Vegan", "spice": "None", "cuisine": "Continental", "servings": 1, "ings": ["Tea Leaves", "Sugar"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            # Desserts
            {"name": "Classic Venetian Tiramisu", "category": "Dessert", "price": 340, "dietary": "Vegetarian", "spice": "None", "cuisine": "Italian", "servings": 1, "ings": ["Cheese", "Coffee Beans", "Sugar", "Flour", "Eggs"], "tags": ["Eggetarian"]},
            {"name": "New York Baked Cheesecake", "category": "Dessert", "price": 310, "dietary": "Vegetarian", "spice": "None", "cuisine": "Continental", "servings": 1, "ings": ["Cheese", "Sugar", "Flour", "Butter"], "tags": ["Vegetarian"]}
        ]

        # Menu 4: South Spice Heritage (South Indian)
        south_menu = [
            # Starters
            {"name": "Crispy Medu Vada (2 pcs)", "category": "Starter", "price": 140, "dietary": "Vegan", "spice": "Low", "cuisine": "South Indian", "servings": 1, "ings": ["Lentils", "Curry Leaves"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            {"name": "Chicken 65 Chennai Express", "category": "Starter", "price": 310, "dietary": "Non-Vegetarian", "spice": "High", "cuisine": "South Indian", "servings": 1, "ings": ["Chicken", "Curry Leaves", "Mustard Seeds"], "tags": ["Non-Vegetarian", "Halal"]},
            {"name": "Gobi 65 Bites", "category": "Starter", "price": 220, "dietary": "Vegan", "spice": "Medium", "cuisine": "South Indian", "servings": 1, "ings": ["Flour", "Curry Leaves"], "tags": ["Vegetarian", "Vegan"]},
            # Mains
            {"name": "Classic Mysore Masala Dosa", "category": "Main Course", "price": 190, "dietary": "Vegan", "spice": "Medium", "cuisine": "South Indian", "servings": 1, "ings": ["Rice", "Lentils", "Potato", "Mustard Seeds"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Steamed Ghee Podi Idli (4 pcs)", "category": "Main Course", "price": 160, "dietary": "Vegetarian", "spice": "Medium", "cuisine": "South Indian", "servings": 1, "ings": ["Rice", "Lentils", "Butter"], "tags": ["Vegetarian"]},
            {"name": "Chettinad Spicy Chicken Curry", "category": "Main Course", "price": 390, "dietary": "Non-Vegetarian", "spice": "Extreme", "cuisine": "South Indian", "servings": 2, "ings": ["Chicken", "Onion", "Tomato", "Coconut"], "tags": ["Non-Vegetarian", "Halal"]},
            {"name": "Malabar Fish Curry with Coconut", "category": "Main Course", "price": 440, "dietary": "Non-Vegetarian", "spice": "High", "cuisine": "South Indian", "servings": 2, "ings": ["Fish", "Coconut", "Curry Leaves", "Mustard Seeds"], "tags": ["Non-Vegetarian"]},
            {"name": "Udupi Sambar & Rice Meal", "category": "Main Course", "price": 210, "dietary": "Vegan", "spice": "Medium", "cuisine": "South Indian", "servings": 2, "ings": ["Rice", "Lentils", "Tomato", "Curry Leaves"], "tags": ["Vegetarian", "Vegan"]},
            # Rice & Breads
            {"name": "Dindigul Thalappakatti Mutton Biryani", "category": "Rice", "price": 490, "dietary": "Non-Vegetarian", "spice": "High", "cuisine": "South Indian", "servings": 2, "ings": ["Rice", "Lamb", "Onion", "Garlic"], "tags": ["Non-Vegetarian", "Halal"]},
            {"name": "South Indian Curd Rice", "category": "Rice", "price": 150, "dietary": "Vegetarian", "spice": "None", "cuisine": "South Indian", "servings": 1, "ings": ["Rice", "Milk", "Mustard Seeds", "Curry Leaves"], "tags": ["Vegetarian"]},
            {"name": "Malabar Parotta (2 pcs)", "category": "Bread", "price": 70, "dietary": "Vegetarian", "spice": "None", "cuisine": "South Indian", "servings": 1, "ings": ["Flour", "Butter"], "tags": ["Vegetarian"]},
            # Beverages
            {"name": "Authentic Kumbakonam Degree Coffee", "category": "Beverage", "price": 90, "dietary": "Vegetarian", "spice": "None", "cuisine": "South Indian", "servings": 1, "ings": ["Coffee Beans", "Milk", "Sugar"], "tags": ["Vegetarian"]},
            {"name": "Spiced Moru Buttermilk", "category": "Beverage", "price": 70, "dietary": "Vegetarian", "spice": "Low", "cuisine": "South Indian", "servings": 1, "ings": ["Milk", "Curry Leaves", "Mustard Seeds"], "tags": ["Vegetarian"]},
            # Desserts
            {"name": "Tirunelveli Halwa", "category": "Dessert", "price": 160, "dietary": "Vegetarian", "spice": "None", "cuisine": "South Indian", "servings": 1, "ings": ["Flour", "Butter", "Sugar", "Cashews"], "tags": ["Vegetarian"]},
            {"name": "Rava Kesari with Cashews", "category": "Dessert", "price": 140, "dietary": "Vegetarian", "spice": "None", "cuisine": "South Indian", "servings": 1, "ings": ["Flour", "Butter", "Sugar", "Cashews"], "tags": ["Vegetarian"]}
        ]

        # Menu 5: Tokyo Umami (Japanese / Other)
        tokyo_menu = [
            # Starters
            {"name": "Steamed Sea Salt Edamame", "category": "Starter", "price": 180, "dietary": "Vegan", "spice": "None", "cuisine": "Other", "servings": 1, "ings": ["Soy Sauce"], "tags": ["Vegetarian", "Vegan", "Jain", "Keto"]},
            {"name": "Pan-Fried Chicken Gyoza (5 pcs)", "category": "Starter", "price": 290, "dietary": "Non-Vegetarian", "spice": "Low", "cuisine": "Other", "servings": 1, "ings": ["Chicken", "Flour", "Garlic", "Soy Sauce"], "tags": ["Non-Vegetarian"]},
            {"name": "Crispy Tofu Agedashi", "category": "Starter", "price": 230, "dietary": "Vegan", "spice": "Low", "cuisine": "Other", "servings": 1, "ings": ["Tofu", "Soy Sauce", "Seaweed"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Classic Tofu Miso Soup", "category": "Starter", "price": 160, "dietary": "Vegetarian", "spice": "None", "cuisine": "Other", "servings": 1, "ings": ["Miso", "Tofu", "Seaweed"], "tags": ["Vegetarian", "Vegan"]},
            # Mains
            {"name": "Rich Tonkotsu Pork Ramen", "category": "Main Course", "price": 490, "dietary": "Non-Vegetarian", "spice": "Medium", "cuisine": "Other", "servings": 1, "ings": ["Pork", "Eggs", "Flour", "Soy Sauce"], "tags": ["Non-Vegetarian"]},
            {"name": "Tokyo Shoyu Chicken Ramen", "category": "Main Course", "price": 440, "dietary": "Non-Vegetarian", "spice": "Low", "cuisine": "Other", "servings": 1, "ings": ["Chicken", "Eggs", "Flour", "Soy Sauce"], "tags": ["Non-Vegetarian", "Halal"]},
            {"name": "Creamy Tofu & Mushroom Miso Ramen", "category": "Main Course", "price": 380, "dietary": "Vegan", "spice": "Low", "cuisine": "Other", "servings": 1, "ings": ["Tofu", "Mushroom", "Flour", "Miso", "Seaweed"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Fresh Salmon Nigiri Platter", "category": "Main Course", "price": 620, "dietary": "Non-Vegetarian", "spice": "None", "cuisine": "Other", "servings": 1, "ings": ["Fish", "Rice", "Seaweed"], "tags": ["Non-Vegetarian", "Keto"]},
            {"name": "Crispy Chicken Katsu Curry Bowl", "category": "Main Course", "price": 410, "dietary": "Non-Vegetarian", "spice": "Medium", "cuisine": "Other", "servings": 1, "ings": ["Chicken", "Flour", "Rice", "Curry Leaves"], "tags": ["Non-Vegetarian"]},
            # Rice & Sides
            {"name": "Japanese Garlic Fried Rice", "category": "Rice", "price": 210, "dietary": "Vegetarian", "spice": "Low", "cuisine": "Other", "servings": 2, "ings": ["Rice", "Garlic", "Butter", "Soy Sauce"], "tags": ["Vegetarian"]},
            {"name": "Steamed Koshihikari Rice", "category": "Rice", "price": 140, "dietary": "Vegan", "spice": "None", "cuisine": "Other", "servings": 2, "ings": ["Rice"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            # Beverages
            {"name": "Iced Ceremonial Matcha Latte", "category": "Beverage", "price": 190, "dietary": "Vegetarian", "spice": "None", "cuisine": "Other", "servings": 1, "ings": ["Matcha", "Milk", "Sugar"], "tags": ["Vegetarian"]},
            {"name": "Warm Roasted Genmaicha Green Tea", "category": "Beverage", "price": 120, "dietary": "Vegan", "spice": "None", "cuisine": "Other", "servings": 1, "ings": ["Tea Leaves"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            # Desserts
            {"name": "Artisan Matcha Ice Cream Scoop", "category": "Dessert", "price": 170, "dietary": "Vegetarian", "spice": "None", "cuisine": "Other", "servings": 1, "ings": ["Matcha", "Milk", "Sugar"], "tags": ["Vegetarian"]},
            {"name": "Assorted Sweet Mochi (3 pcs)", "category": "Dessert", "price": 210, "dietary": "Vegan", "spice": "None", "cuisine": "Other", "servings": 1, "ings": ["Rice", "Sugar"], "tags": ["Vegetarian", "Vegan", "Jain"]}
        ]

        # Menu 6: Green Haven Cafe (Plant-Forward / Wholesome Vegan & Vegetarian)
        green_menu = [
            # Starters
            {"name": "Avocado Sourdough Tartine", "category": "Starter", "price": 240, "dietary": "Vegan", "spice": "None", "cuisine": "Continental", "servings": 1, "ings": ["Flour", "Avocado", "Olive Oil", "Tomato"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Baked Herbed Falafel Bites", "category": "Starter", "price": 210, "dietary": "Vegan", "spice": "Low", "cuisine": "Continental", "servings": 1, "ings": ["Lentils", "Garlic", "Olive Oil"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Crispy Cauliflower Buffalo Wings", "category": "Starter", "price": 230, "dietary": "Vegan", "spice": "High", "cuisine": "Continental", "servings": 1, "ings": ["Flour", "Garlic"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Whipped Feta & Wild Mushroom Crostini", "category": "Starter", "price": 260, "dietary": "Vegetarian", "spice": "None", "cuisine": "Continental", "servings": 1, "ings": ["Flour", "Cheese", "Mushroom", "Olive Oil"], "tags": ["Vegetarian"]},
            # Mains
            {"name": "Green Goddess Quinoa Buddha Bowl", "category": "Main Course", "price": 360, "dietary": "Vegan", "spice": "None", "cuisine": "Continental", "servings": 1, "ings": ["Rice", "Avocado", "Tofu", "Olive Oil"], "tags": ["Vegetarian", "Vegan", "Jain", "Keto"]},
            {"name": "Grilled Halloumi & Roasted Vegetable Bowl", "category": "Main Course", "price": 370, "dietary": "Vegetarian", "spice": "Low", "cuisine": "Continental", "servings": 1, "ings": ["Rice", "Cheese", "Bell Pepper", "Olive Oil", "Tomato"], "tags": ["Vegetarian"]},
            {"name": "Smoky Jackfruit Pulled Carnitas Bowl", "category": "Main Course", "price": 380, "dietary": "Vegan", "spice": "Medium", "cuisine": "Continental", "servings": 1, "ings": ["Rice", "Black Beans", "Tomato", "Corn"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Creamy Cashew Vegan Mac & Cheese", "category": "Main Course", "price": 350, "dietary": "Vegan", "spice": "Low", "cuisine": "Continental", "servings": 1, "ings": ["Flour", "Cashews", "Mustard Seeds"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Wild Mushroom & Burrata Truffle Pasta", "category": "Main Course", "price": 390, "dietary": "Vegetarian", "spice": "None", "cuisine": "Italian", "servings": 1, "ings": ["Flour", "Cheese", "Butter", "Mushroom"], "tags": ["Vegetarian"]},
            {"name": "Grilled Vegan Basil Pesto Pasta", "category": "Main Course", "price": 340, "dietary": "Vegan", "spice": "None", "cuisine": "Italian", "servings": 1, "ings": ["Flour", "Basil", "Olive Oil", "Garlic"], "tags": ["Vegetarian", "Vegan"]},
            # Sides
            {"name": "Baked Sweet Potato Wedges", "category": "Side", "price": 160, "dietary": "Vegan", "spice": "None", "cuisine": "Continental", "servings": 1, "ings": ["Potato", "Olive Oil"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            {"name": "Parmesan Herb Polenta Fries", "category": "Side", "price": 180, "dietary": "Vegetarian", "spice": "None", "cuisine": "Continental", "servings": 1, "ings": ["Flour", "Cheese", "Olive Oil"], "tags": ["Vegetarian"]},
            # Beverages
            {"name": "Cold-Pressed Detox Green Juice", "category": "Beverage", "price": 160, "dietary": "Vegan", "spice": "None", "cuisine": "Beverages", "servings": 1, "ings": [], "tags": ["Vegetarian", "Vegan", "Jain"]},
            {"name": "Golden Turmeric Oat Milk Latte", "category": "Beverage", "price": 180, "dietary": "Vegan", "spice": "None", "cuisine": "Beverages", "servings": 1, "ings": [], "tags": ["Vegetarian", "Vegan", "Jain"]},
            {"name": "Organic Honey & Vanilla Cappuccino", "category": "Beverage", "price": 170, "dietary": "Vegetarian", "spice": "None", "cuisine": "Beverages", "servings": 1, "ings": ["Coffee Beans", "Milk", "Sugar"], "tags": ["Vegetarian"]},
            # Desserts
            {"name": "Raw Dark Cacao Energy Truffles", "category": "Dessert", "price": 190, "dietary": "Vegan", "spice": "None", "cuisine": "Desserts", "servings": 1, "ings": ["Almonds", "Sugar"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            {"name": "Greek Yogurt & Forest Berry Parfait", "category": "Dessert", "price": 210, "dietary": "Vegetarian", "spice": "None", "cuisine": "Desserts", "servings": 1, "ings": ["Milk", "Sugar", "Almonds"], "tags": ["Vegetarian"]},
            {"name": "Coconut Berry Chia Seed Parfait", "category": "Dessert", "price": 220, "dietary": "Vegan", "spice": "None", "cuisine": "Desserts", "servings": 1, "ings": ["Coconut", "Sugar"], "tags": ["Vegetarian", "Vegan", "Jain"]}
        ]

        menus = [
            (restaurants[0], spice_menu),
            (restaurants[1], dragon_menu),
            (restaurants[2], grand_menu),
            (restaurants[3], south_menu),
            (restaurants[4], tokyo_menu),
            (restaurants[5], green_menu),
        ]

        total_items_seeded = 0
        for restaurant, menu_items in menus:
            for item in menu_items:
                mi = MenuItem(
                    restaurant_id=restaurant.id,
                    name=item["name"],
                    category=item["category"],
                    price=item["price"],
                    dietary_preference=item["dietary"],
                    spice_level=item["spice"],
                    cuisine=item["cuisine"],
                    serving_size=item.get("servings", 1),
                    is_available=True,
                    description=f"Freshly prepared {item['name']} featuring signature house recipe and quality ingredients.",
                    image_url=CATEGORY_IMAGES.get(item["category"], "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500&q=80")
                )
                session.add(mi)
                await session.flush()
                total_items_seeded += 1

                for ing_name in item.get("ings", []):
                    if ing_name in ingredients:
                        session.add(MenuItemIngredient(menu_item_id=mi.id, ingredient_id=ingredients[ing_name].id))

                for tag_name in item.get("tags", []):
                    if tag_name in tags:
                        session.add(MenuItemTag(menu_item_id=mi.id, tag_id=tags[tag_name].id))

        await session.commit()
        print(f"Successfully seeded {total_items_seeded} unique, realistic menu items across {len(restaurants)} restaurants.")

        # 6. Create Admin Users (Platform + Restaurant Managers)
        admin_emails = [
            ("platform@smartdiner.com", "admin123", "PLATFORM_ADMIN", None),
            ("manager@smartdiner.com", "manager123", "RESTAURANT_ADMIN", str(restaurants[0].id)),
            ("manager.spice@smartdiner.com", "manager123", "RESTAURANT_ADMIN", str(restaurants[0].id)),
            ("manager.dragon@smartdiner.com", "manager123", "RESTAURANT_ADMIN", str(restaurants[1].id)),
            ("manager.grand@smartdiner.com", "manager123", "RESTAURANT_ADMIN", str(restaurants[2].id)),
            ("manager.south@smartdiner.com", "manager123", "RESTAURANT_ADMIN", str(restaurants[3].id)),
            ("manager.tokyo@smartdiner.com", "manager123", "RESTAURANT_ADMIN", str(restaurants[4].id)),
            ("manager.green@smartdiner.com", "manager123", "RESTAURANT_ADMIN", str(restaurants[5].id)),
        ]

        for email, password, role, rest_id in admin_emails:
            res = await session.execute(select(AdminUser).where(AdminUser.email == email))
            existing = res.scalars().first()
            if not existing:
                admin_user = AdminUser(
                    email=email,
                    password_hash=get_password_hash(password),
                    role=role,
                    restaurant_id=rest_id
                )
                session.add(admin_user)

        await session.commit()
        print("Admin users seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())

import asyncio
import random
import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.config import settings
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem
from app.models.allergen import Allergen
from app.models.ingredient import Ingredient, MenuItemIngredient, IngredientAllergen
from app.models.dietary_tag import DietaryTag, MenuItemTag
from app.models.admin_user import AdminUser
from app.services.auth import get_password_hash
from app.database import Base, engine, AsyncSessionLocal

async def seed():
    async with AsyncSessionLocal() as session:
        # Check if we already have data
        result = await session.execute(select(Restaurant).limit(1))
        if result.scalar_one_or_none():
            print("Database already has data. Run docker compose down -v if you want a fresh start. Exiting.")
            return

        print("Starting massive seed...")

        # 1. Create Restaurants
        restaurants_data = [
            {
                "name": "Spice Garden", 
                "description": "Authentic flavors from across India, featuring aromatic curries, tandoori specials, and traditional sweets crafted with age-old recipes.",
                "address": "123 Curry Lane", 
                "cuisine_type": "North Indian", 
                "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500&q=80"
            },
            {
                "name": "Dragon's Wok", 
                "description": "A fusion of classic wok-tossed recipes and modern Asian delicacies, bringing the vibrant and fiery tastes of the Orient straight to your table.",
                "address": "456 Silk Road", 
                "cuisine_type": "Chinese", 
                "image_url": "https://images.unsplash.com/photo-1552566626-52f8b828add9?w=500&q=80"
            },
            {
                "name": "The Grand Kitchen", 
                "description": "A global culinary journey under one roof, offering exquisite continental, Italian, and intercontinental dishes prepared by master chefs.",
                "address": "789 Main St", 
                "cuisine_type": "Other", 
                "image_url": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=500&q=80"
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
            "Mustard Seeds": ["Mustard"], "Curry Leaves": [], "Soba Noodles": ["Gluten"], "Lamb": [], "Beef": [], "Pork": []
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

        # Helper to generate items
        def make_items(restaurant, prefix, base_items, counts):
            category_images = {
                "Starter": "https://images.unsplash.com/photo-1541529086526-db283c563270?w=500&q=80",
                "Main Course": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500&q=80",
                "Bread": "https://images.unsplash.com/photo-1601050690597-df0568a70950?w=500&q=80",
                "Rice": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?w=500&q=80",
                "Beverage": "https://images.unsplash.com/photo-1544145945-f90425340c7e?w=500&q=80",
                "Dessert": "https://images.unsplash.com/photo-1551024601-bec78aea704b?w=500&q=80",
                "Side": "https://images.unsplash.com/photo-1628294895950-9805252327bc?w=500&q=80",
                "Combo": "https://images.unsplash.com/photo-1610440042657-612c34d95e9f?w=500&q=80",
                "Fast Food": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=500&q=80"
            }
            items = []
            for item in base_items:
                for i in range(counts.get(item['category'], 2)):
                    name = f"{prefix} {item['name']} {i+1}"
                    price = item['base_price'] + random.randint(-40, 100)
                    if price < 50: price = 50
                    
                    # Randomize some attributes for diversity
                    is_avail = random.random() > 0.05 # ~5% unavailable
                    
                    mi = MenuItem(
                        restaurant_id=restaurant.id,
                        name=name,
                        category=item['category'],
                        price=price,
                        is_veg=item['is_veg'],
                        spice_level=item['spice_level'],
                        cuisine=item['cuisine'],
                        serving_size=item.get('serving_size', 1),
                        is_available=is_avail,
                        description=f"Delicious and authentic {name}, prepared fresh with premium ingredients. Perfect for your cravings.",
                        image_url=category_images.get(item['category'], "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500&q=80")
                    )
                    items.append((mi, item['ingredients'], item['tags']))
            return items

        # Diverse base menus
        base_indian = [
            # Starters
            {"name": "Paneer Tikka", "category": "Starter", "base_price": 280, "is_veg": True, "spice_level": "Medium", "cuisine": "North Indian", "ingredients": ["Paneer", "Onion", "Bell Pepper"], "tags": ["Vegetarian"]},
            {"name": "Chicken Tikka", "category": "Starter", "base_price": 320, "is_veg": False, "spice_level": "High", "cuisine": "North Indian", "ingredients": ["Chicken", "Onion", "Mustard Seeds"], "tags": ["Non-Vegetarian"]},
            {"name": "Mushroom Tikka", "category": "Starter", "base_price": 260, "is_veg": True, "spice_level": "Medium", "cuisine": "North Indian", "ingredients": ["Mushroom", "Onion", "Tomato"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Gobi Manchurian", "category": "Starter", "base_price": 220, "is_veg": True, "spice_level": "Medium", "cuisine": "Indo-Chinese", "ingredients": ["Flour", "Soy Sauce", "Garlic"], "tags": ["Vegetarian", "Vegan"]},
            
            # Mains
            {"name": "Dal Makhani", "category": "Main Course", "base_price": 250, "is_veg": True, "spice_level": "Low", "cuisine": "North Indian", "ingredients": ["Lentils", "Butter", "Tomato"], "tags": ["Vegetarian"]},
            {"name": "Dal Tadka", "category": "Main Course", "base_price": 210, "is_veg": True, "spice_level": "Medium", "cuisine": "North Indian", "ingredients": ["Lentils", "Garlic", "Tomato"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Butter Chicken", "category": "Main Course", "base_price": 380, "is_veg": False, "spice_level": "Medium", "cuisine": "North Indian", "ingredients": ["Chicken", "Butter", "Tomato", "Cashews"], "tags": ["Non-Vegetarian"]},
            {"name": "Mutton Rogan Josh", "category": "Main Course", "base_price": 450, "is_veg": False, "spice_level": "High", "cuisine": "North Indian", "ingredients": ["Lamb", "Onion", "Garlic"], "tags": ["Non-Vegetarian", "Halal"]},
            {"name": "Palak Paneer", "category": "Main Course", "base_price": 290, "is_veg": True, "spice_level": "Low", "cuisine": "North Indian", "ingredients": ["Paneer", "Garlic", "Tomato"], "tags": ["Vegetarian"]},
            {"name": "Jain Paneer Masala", "category": "Main Course", "base_price": 310, "is_veg": True, "spice_level": "Low", "cuisine": "North Indian", "ingredients": ["Paneer", "Tomato", "Cashews"], "tags": ["Vegetarian", "Jain"]},
            {"name": "Masala Dosa", "category": "Main Course", "base_price": 180, "is_veg": True, "spice_level": "Medium", "cuisine": "South Indian", "ingredients": ["Rice", "Lentils", "Potato", "Mustard Seeds"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Idli Sambhar", "category": "Main Course", "base_price": 140, "is_veg": True, "spice_level": "Low", "cuisine": "South Indian", "ingredients": ["Rice", "Lentils", "Curry Leaves"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            
            # Breads
            {"name": "Butter Naan", "category": "Bread", "base_price": 60, "is_veg": True, "spice_level": "None", "cuisine": "North Indian", "ingredients": ["Flour", "Butter"], "tags": ["Vegetarian"]},
            {"name": "Garlic Naan", "category": "Bread", "base_price": 75, "is_veg": True, "spice_level": "None", "cuisine": "North Indian", "ingredients": ["Flour", "Butter", "Garlic"], "tags": ["Vegetarian"]},
            {"name": "Tandoori Roti", "category": "Bread", "base_price": 40, "is_veg": True, "spice_level": "None", "cuisine": "North Indian", "ingredients": ["Flour"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            
            # Rice
            {"name": "Chicken Biryani", "category": "Rice", "base_price": 420, "is_veg": False, "spice_level": "Medium", "cuisine": "North Indian", "serving_size": 2, "ingredients": ["Rice", "Chicken", "Onion", "Cashews"], "tags": ["Non-Vegetarian", "Halal"]},
            {"name": "Mutton Biryani", "category": "Rice", "base_price": 520, "is_veg": False, "spice_level": "High", "cuisine": "North Indian", "serving_size": 2, "ingredients": ["Rice", "Lamb", "Onion", "Garlic"], "tags": ["Non-Vegetarian", "Halal"]},
            {"name": "Veg Pulao", "category": "Rice", "base_price": 240, "is_veg": True, "spice_level": "Low", "cuisine": "North Indian", "ingredients": ["Rice", "Cashews", "Onion"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Steamed Rice", "category": "Rice", "base_price": 120, "is_veg": True, "spice_level": "None", "cuisine": "North Indian", "ingredients": ["Rice"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            
            # Sides, Beverages, Desserts
            {"name": "Mixed Raita", "category": "Side", "base_price": 100, "is_veg": True, "spice_level": "None", "cuisine": "North Indian", "serving_size": 2, "ingredients": ["Milk", "Onion", "Tomato"], "tags": ["Vegetarian"]},
            {"name": "Masala Chai", "category": "Beverage", "base_price": 80, "is_veg": True, "spice_level": "None", "cuisine": "North Indian", "ingredients": ["Tea Leaves", "Milk", "Sugar"], "tags": ["Vegetarian"]},
            {"name": "Sweet Lassi", "category": "Beverage", "base_price": 110, "is_veg": True, "spice_level": "None", "cuisine": "North Indian", "ingredients": ["Milk", "Sugar"], "tags": ["Vegetarian"]},
            {"name": "Gulab Jamun", "category": "Dessert", "base_price": 160, "is_veg": True, "spice_level": "None", "cuisine": "North Indian", "serving_size": 2, "ingredients": ["Flour", "Milk", "Sugar"], "tags": ["Vegetarian"]},
            {"name": "Rasmalai", "category": "Dessert", "base_price": 200, "is_veg": True, "spice_level": "None", "cuisine": "North Indian", "serving_size": 2, "ingredients": ["Paneer", "Milk", "Sugar", "Almonds"], "tags": ["Vegetarian"]}
        ]

        base_chinese = [
            # Starters
            {"name": "Spring Roll", "category": "Starter", "base_price": 200, "is_veg": True, "spice_level": "Low", "cuisine": "Chinese", "ingredients": ["Flour", "Onion", "Tomato"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Chicken 65", "category": "Starter", "base_price": 280, "is_veg": False, "spice_level": "Extreme", "cuisine": "Chinese", "ingredients": ["Chicken", "Garlic"], "tags": ["Non-Vegetarian", "Halal"]},
            {"name": "Chilli Paneer", "category": "Starter", "base_price": 260, "is_veg": True, "spice_level": "High", "cuisine": "Indo-Chinese", "ingredients": ["Paneer", "Soy Sauce", "Bell Pepper"], "tags": ["Vegetarian"]},
            {"name": "Prawn Crackers", "category": "Starter", "base_price": 150, "is_veg": False, "spice_level": "Low", "cuisine": "Chinese", "ingredients": ["Shrimp", "Flour"], "tags": ["Non-Vegetarian"]},
            {"name": "Egg Drop Soup", "category": "Starter", "base_price": 150, "is_veg": False, "spice_level": "Low", "cuisine": "Chinese", "ingredients": ["Eggs", "Onion"], "tags": ["Eggetarian"]},
            
            # Mains
            {"name": "Kung Pao Chicken", "category": "Main Course", "base_price": 340, "is_veg": False, "spice_level": "High", "cuisine": "Chinese", "ingredients": ["Chicken", "Soy Sauce", "Peanut Butter"], "tags": ["Non-Vegetarian"]},
            {"name": "Sweet & Sour Pork", "category": "Main Course", "base_price": 380, "is_veg": False, "spice_level": "Medium", "cuisine": "Chinese", "ingredients": ["Pork", "Sugar", "Bell Pepper", "Onion"], "tags": ["Non-Vegetarian"]},
            {"name": "Mapo Tofu", "category": "Main Course", "base_price": 290, "is_veg": True, "spice_level": "Extreme", "cuisine": "Chinese", "ingredients": ["Tofu", "Soy Sauce", "Garlic", "Sesame Oil"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Shrimp Chow Mein", "category": "Main Course", "base_price": 350, "is_veg": False, "spice_level": "Medium", "cuisine": "Chinese", "ingredients": ["Flour", "Shrimp", "Soy Sauce", "Onion"], "tags": ["Non-Vegetarian"]},
            {"name": "Vegetable Hakka Noodles", "category": "Main Course", "base_price": 240, "is_veg": True, "spice_level": "Low", "cuisine": "Indo-Chinese", "ingredients": ["Flour", "Soy Sauce", "Bell Pepper"], "tags": ["Vegetarian", "Vegan"]},
            
            # Rice
            {"name": "Egg Fried Rice", "category": "Rice", "base_price": 220, "is_veg": False, "spice_level": "Low", "cuisine": "Chinese", "ingredients": ["Rice", "Soy Sauce", "Eggs", "Onion"], "tags": ["Eggetarian"]},
            {"name": "Chicken Fried Rice", "category": "Rice", "base_price": 260, "is_veg": False, "spice_level": "Medium", "cuisine": "Chinese", "ingredients": ["Rice", "Soy Sauce", "Chicken", "Onion"], "tags": ["Non-Vegetarian"]},
            {"name": "Veg Garlic Fried Rice", "category": "Rice", "base_price": 210, "is_veg": True, "spice_level": "Medium", "cuisine": "Chinese", "ingredients": ["Rice", "Soy Sauce", "Garlic"], "tags": ["Vegetarian", "Vegan"]},
            
            # Beverages, Desserts
            {"name": "Jasmine Tea", "category": "Beverage", "base_price": 120, "is_veg": True, "spice_level": "None", "cuisine": "Chinese", "ingredients": ["Tea Leaves"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            {"name": "Boba Milk Tea", "category": "Beverage", "base_price": 180, "is_veg": True, "spice_level": "None", "cuisine": "Chinese", "ingredients": ["Tea Leaves", "Milk", "Sugar"], "tags": ["Vegetarian"]},
            {"name": "Fried Ice Cream", "category": "Dessert", "base_price": 220, "is_veg": True, "spice_level": "None", "cuisine": "Chinese", "ingredients": ["Milk", "Flour", "Sugar"], "tags": ["Vegetarian"]},
        ]

        base_other = [
            # Starters
            {"name": "Classic Bruschetta", "category": "Starter", "base_price": 220, "is_veg": True, "spice_level": "Low", "cuisine": "Italian", "ingredients": ["Flour", "Tomato", "Garlic", "Olive Oil", "Basil"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Garlic Bread with Cheese", "category": "Bread", "base_price": 180, "is_veg": True, "spice_level": "None", "cuisine": "Italian", "ingredients": ["Flour", "Garlic", "Butter", "Cheese"], "tags": ["Vegetarian"]},
            {"name": "Caesar Salad", "category": "Starter", "base_price": 250, "is_veg": True, "spice_level": "None", "cuisine": "Continental", "ingredients": ["Cheese", "Olive Oil", "Garlic"], "tags": ["Vegetarian", "Keto"]},
            {"name": "Chicken Caesar Salad", "category": "Starter", "base_price": 320, "is_veg": False, "spice_level": "None", "cuisine": "Continental", "ingredients": ["Chicken", "Cheese", "Olive Oil", "Garlic"], "tags": ["Non-Vegetarian", "Keto"]},
            
            # Mains
            {"name": "Margherita Pizza", "category": "Main Course", "base_price": 450, "is_veg": True, "spice_level": "None", "cuisine": "Italian", "serving_size": 2, "ingredients": ["Flour", "Tomato", "Cheese", "Olive Oil", "Basil"], "tags": ["Vegetarian"]},
            {"name": "Pepperoni Pizza", "category": "Main Course", "base_price": 550, "is_veg": False, "spice_level": "Medium", "cuisine": "Italian", "serving_size": 2, "ingredients": ["Flour", "Tomato", "Cheese", "Beef"], "tags": ["Non-Vegetarian"]},
            {"name": "Spaghetti Bolognese", "category": "Main Course", "base_price": 420, "is_veg": False, "spice_level": "Low", "cuisine": "Italian", "ingredients": ["Flour", "Tomato", "Beef", "Garlic", "Olive Oil"], "tags": ["Non-Vegetarian"]},
            {"name": "Penne Arrabbiata", "category": "Main Course", "base_price": 380, "is_veg": True, "spice_level": "High", "cuisine": "Italian", "ingredients": ["Flour", "Tomato", "Garlic", "Olive Oil", "Basil"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Grilled Salmon", "category": "Main Course", "base_price": 750, "is_veg": False, "spice_level": "Low", "cuisine": "Continental", "ingredients": ["Fish", "Olive Oil", "Garlic"], "tags": ["Non-Vegetarian", "Keto"]},
            {"name": "Beef Steak", "category": "Main Course", "base_price": 850, "is_veg": False, "spice_level": "Medium", "cuisine": "Continental", "ingredients": ["Beef", "Olive Oil", "Garlic", "Butter"], "tags": ["Non-Vegetarian", "Keto"]},
            {"name": "Mushroom Risotto", "category": "Main Course", "base_price": 480, "is_veg": True, "spice_level": "Low", "cuisine": "Italian", "ingredients": ["Rice", "Mushroom", "Cheese", "Butter"], "tags": ["Vegetarian"]},
            
            # Sides, Beverages, Desserts
            {"name": "French Fries", "category": "Side", "base_price": 150, "is_veg": True, "spice_level": "None", "cuisine": "Fast Food", "ingredients": ["Potato", "Olive Oil"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Tiramisu", "category": "Dessert", "base_price": 350, "is_veg": True, "spice_level": "None", "cuisine": "Italian", "ingredients": ["Cheese", "Coffee Beans", "Sugar", "Flour", "Eggs"], "tags": ["Eggetarian"]},
            {"name": "Cheesecake", "category": "Dessert", "base_price": 320, "is_veg": True, "spice_level": "None", "cuisine": "Continental", "ingredients": ["Cheese", "Sugar", "Flour", "Butter"], "tags": ["Vegetarian"]},
            {"name": "Espresso", "category": "Beverage", "base_price": 120, "is_veg": True, "spice_level": "None", "cuisine": "Italian", "ingredients": ["Coffee Beans"], "tags": ["Vegetarian", "Vegan", "Jain"]},
            {"name": "Cappuccino", "category": "Beverage", "base_price": 180, "is_veg": True, "spice_level": "None", "cuisine": "Italian", "ingredients": ["Coffee Beans", "Milk", "Sugar"], "tags": ["Vegetarian"]}
        ]
        
        # Massive Expansion: generate ~85 items per restaurant!
        ind_counts = {"Starter": 7, "Main Course": 10, "Bread": 6, "Rice": 6, "Beverage": 5, "Dessert": 5, "Side": 5}
        chin_counts = {"Starter": 8, "Main Course": 12, "Rice": 8, "Beverage": 5, "Dessert": 5}
        oth_counts = {"Starter": 7, "Main Course": 10, "Bread": 5, "Side": 5, "Beverage": 6, "Dessert": 6}

        all_items_to_add = []
        all_items_to_add.extend(make_items(restaurants[0], "Spice", base_indian, ind_counts))
        all_items_to_add.extend(make_items(restaurants[1], "Dragon", base_chinese, chin_counts))
        all_items_to_add.extend(make_items(restaurants[2], "Grand", base_other, oth_counts))
        
        for mi, ings, tgs in all_items_to_add:
            session.add(mi)
            await session.flush()
            for ing_name in ings:
                session.add(MenuItemIngredient(menu_item_id=mi.id, ingredient_id=ingredients[ing_name].id))
            for tag_name in tgs:
                session.add(MenuItemTag(menu_item_id=mi.id, tag_id=tags[tag_name].id))
        
        await session.commit()
        print(f"Successfully seeded {len(all_items_to_add)} menu items across {len(restaurants)} restaurants.")

        # 5. Create Admin Users
        result = await session.execute(select(AdminUser).where(AdminUser.email == "platform@smartdiner.com"))
        platform_admin = result.scalars().first()
        if not platform_admin:
            platform_admin = AdminUser(
                email="platform@smartdiner.com",
                password_hash=get_password_hash("admin123"),
                role="PLATFORM_ADMIN",
                restaurant_id=None
            )
            session.add(platform_admin)

        if restaurants:
            result = await session.execute(select(AdminUser).where(AdminUser.email == "manager@smartdiner.com"))
            restaurant_admin = result.scalars().first()
            if not restaurant_admin:
                restaurant_admin = AdminUser(
                    email="manager@smartdiner.com",
                    password_hash=get_password_hash("manager123"),
                    role="RESTAURANT_ADMIN",
                    restaurant_id=str(restaurants[0].id)
                )
                session.add(restaurant_admin)
        
        await session.commit()
        print("Admin users seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())

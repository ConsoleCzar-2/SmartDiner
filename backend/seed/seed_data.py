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
            print("Database already has data. Exiting.")
            return

        print("Starting seed...")

        # 1. Create Restaurants
        restaurants_data = [
            {"name": "Spice Garden", "address": "123 Curry Lane", "cuisine_type": "North Indian", "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500&q=80"},
            {"name": "Dragon's Wok", "address": "456 Silk Road", "cuisine_type": "Chinese", "image_url": "https://images.unsplash.com/photo-1552566626-52f8b828add9?w=500&q=80"},
            {"name": "The Grand Kitchen", "address": "789 Main St", "cuisine_type": "Other", "image_url": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=500&q=80"}
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
        allergen_names = ["Peanuts", "Tree Nuts", "Dairy", "Gluten", "Soy", "Shellfish", "Eggs", "Sesame", "Fish"]
        allergens = {}
        for name in allergen_names:
            a = Allergen(name=name)
            session.add(a)
            allergens[name] = a
        await session.commit()

        # 3. Create Dietary Tags
        tag_names = ["Vegetarian", "Vegan", "Jain", "Eggetarian", "Non-Vegetarian"]
        tags = {}
        for name in tag_names:
            t = DietaryTag(name=name)
            session.add(t)
            tags[name] = t
        await session.commit()

        # 4. Create Ingredients & map to allergens
        ingredients_data = {
            "Chicken": [],
            "Paneer": ["Dairy"],
            "Milk": ["Dairy"],
            "Butter": ["Dairy"],
            "Flour": ["Gluten"],
            "Rice": [],
            "Eggs": ["Eggs"],
            "Peanut Butter": ["Peanuts"],
            "Soy Sauce": ["Soy", "Gluten"],
            "Shrimp": ["Shellfish"],
            "Fish": ["Fish"],
            "Cashews": ["Tree Nuts"],
            "Sesame Oil": ["Sesame"],
            "Onion": [],
            "Garlic": [],
            "Tomato": [],
            "Lentils": [],
            "Potato": [],
            "Sugar": [],
            "Tea Leaves": []
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
            items = []
            for item in base_items:
                for i in range(counts.get(item['category'], 2)):
                    # Varing name, price
                    name = f"{prefix} {item['name']} {i+1}"
                    price = item['base_price'] + random.randint(-20, 50)
                    if price < 0: price = 10
                    mi = MenuItem(
                        restaurant_id=restaurant.id,
                        name=name,
                        category=item['category'],
                        price=price,
                        is_veg=item['is_veg'],
                        spice_level=item['spice_level'],
                        cuisine=item['cuisine'],
                        serving_size=item.get('serving_size', 1),
                        is_available=random.random() > 0.1 # ~10% unavailable
                    )
                    items.append((mi, item['ingredients'], item['tags']))
            return items

        base_indian = [
            {"name": "Paneer Tikka", "category": "Starter", "base_price": 250, "is_veg": True, "spice_level": "Medium", "cuisine": "North Indian", "ingredients": ["Paneer", "Onion"], "tags": ["Vegetarian"]},
            {"name": "Dal Makhani", "category": "Main Course", "base_price": 250, "is_veg": True, "spice_level": "Low", "cuisine": "North Indian", "ingredients": ["Lentils", "Butter", "Tomato"], "tags": ["Vegetarian"]},
            {"name": "Butter Chicken", "category": "Main Course", "base_price": 350, "is_veg": False, "spice_level": "Medium", "cuisine": "North Indian", "ingredients": ["Chicken", "Butter", "Tomato"], "tags": ["Non-Vegetarian"]},
            {"name": "Butter Naan", "category": "Bread", "base_price": 60, "is_veg": True, "spice_level": "None", "cuisine": "North Indian", "ingredients": ["Flour", "Butter"], "tags": ["Vegetarian"]},
            {"name": "Chicken Biryani", "category": "Rice", "base_price": 380, "is_veg": False, "spice_level": "Medium", "cuisine": "North Indian", "serving_size": 2, "ingredients": ["Rice", "Chicken", "Onion"], "tags": ["Non-Vegetarian"]},
            {"name": "Masala Chai", "category": "Beverage", "base_price": 80, "is_veg": True, "spice_level": "None", "cuisine": "North Indian", "ingredients": ["Tea Leaves", "Milk", "Sugar"], "tags": ["Vegetarian"]},
            {"name": "Gulab Jamun", "category": "Dessert", "base_price": 150, "is_veg": True, "spice_level": "None", "cuisine": "North Indian", "serving_size": 2, "ingredients": ["Flour", "Milk", "Sugar"], "tags": ["Vegetarian"]},
            {"name": "Mixed Raita", "category": "Side", "base_price": 120, "is_veg": True, "spice_level": "None", "cuisine": "North Indian", "serving_size": 2, "ingredients": ["Milk", "Onion"], "tags": ["Vegetarian"]},
            {"name": "Jain Paneer", "category": "Main Course", "base_price": 280, "is_veg": True, "spice_level": "Low", "cuisine": "North Indian", "ingredients": ["Paneer", "Tomato"], "tags": ["Vegetarian", "Jain"]},
        ]

        base_chinese = [
            {"name": "Spring Roll", "category": "Starter", "base_price": 180, "is_veg": True, "spice_level": "Low", "cuisine": "Chinese", "ingredients": ["Flour", "Onion", "Tomato"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Chicken 65", "category": "Starter", "base_price": 280, "is_veg": False, "spice_level": "High", "cuisine": "Chinese", "ingredients": ["Chicken", "Garlic"], "tags": ["Non-Vegetarian"]},
            {"name": "Kung Pao Chicken", "category": "Main Course", "base_price": 320, "is_veg": False, "spice_level": "High", "cuisine": "Chinese", "ingredients": ["Chicken", "Soy Sauce", "Peanut Butter"], "tags": ["Non-Vegetarian"]},
            {"name": "Fried Rice", "category": "Rice", "base_price": 220, "is_veg": True, "spice_level": "Low", "cuisine": "Chinese", "ingredients": ["Rice", "Soy Sauce", "Onion"], "tags": ["Vegetarian", "Vegan"]},
            {"name": "Shrimp Noodles", "category": "Main Course", "base_price": 350, "is_veg": False, "spice_level": "Medium", "cuisine": "Chinese", "ingredients": ["Flour", "Shrimp", "Soy Sauce"], "tags": ["Non-Vegetarian"]},
            {"name": "Egg Drop Soup", "category": "Starter", "base_price": 150, "is_veg": False, "spice_level": "Low", "cuisine": "Chinese", "ingredients": ["Eggs", "Onion"], "tags": ["Eggetarian"]},
        ]

        base_other = [
            {"name": "Fish and Chips", "category": "Main Course", "base_price": 400, "is_veg": False, "spice_level": "None", "cuisine": "Other", "ingredients": ["Fish", "Potato", "Flour"], "tags": ["Non-Vegetarian"]},
            {"name": "Garlic Bread", "category": "Bread", "base_price": 120, "is_veg": True, "spice_level": "None", "cuisine": "Other", "ingredients": ["Flour", "Garlic", "Butter"], "tags": ["Vegetarian"]},
            {"name": "Cashew Salad", "category": "Starter", "base_price": 200, "is_veg": True, "spice_level": "None", "cuisine": "Other", "ingredients": ["Cashews", "Tomato", "Onion"], "tags": ["Vegetarian", "Vegan"]},
        ]
        
        # Adjust counts to get ~27-30 items per restaurant
        ind_counts = {"Starter": 3, "Main Course": 4, "Bread": 4, "Rice": 4, "Beverage": 3, "Dessert": 3, "Side": 3}
        chin_counts = {"Starter": 5, "Main Course": 8, "Rice": 5}
        oth_counts = {"Starter": 10, "Main Course": 10, "Bread": 10}

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

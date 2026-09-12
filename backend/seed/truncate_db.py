import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.database import AsyncSessionLocal

async def truncate(session_factory=None):
    factory = session_factory or AsyncSessionLocal
    async with factory() as session:
        print("Truncating tables to prepare for seed...")
        
        # We use CASCADE to drop dependent rows in link tables (e.g., menu_item_ingredients, order_items)
        try:
            await session.execute(text("TRUNCATE TABLE orders, conversations, restaurants, allergens, dietary_tags, ingredients, admin_users CASCADE;"))
        except Exception:
            # Fallback if some optional tables don't exist yet
            await session.execute(text("TRUNCATE TABLE restaurants, allergens, dietary_tags, ingredients, admin_users CASCADE;"))
            
        await session.commit()
        print("Database truncated successfully. You can now run the seed script.")

if __name__ == "__main__":
    asyncio.run(truncate())

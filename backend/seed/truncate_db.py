import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def truncate():
    async with AsyncSessionLocal() as session:
        print("Truncating tables to prepare for massive seed...")
        
        # We use CASCADE to drop dependent rows in link tables (e.g., menu_item_ingredients)
        await session.execute(text("TRUNCATE TABLE restaurants CASCADE;"))
        await session.execute(text("TRUNCATE TABLE allergens CASCADE;"))
        await session.execute(text("TRUNCATE TABLE dietary_tags CASCADE;"))
        await session.execute(text("TRUNCATE TABLE ingredients CASCADE;"))
        await session.execute(text("TRUNCATE TABLE admin_users CASCADE;"))
        
        await session.commit()
        print("Database truncated successfully. You can now run the seed script.")

if __name__ == "__main__":
    asyncio.run(truncate())

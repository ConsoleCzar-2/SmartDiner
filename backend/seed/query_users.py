"""
Read-only utility to query customer users and admin users from Render (or local) PostgreSQL.

Usage:
  python -m seed.query_users --url="postgresql://user:password@host.render.com/dbname"
  or (uses DATABASE_URL or RENDER_DATABASE_URL from environment/.env)
  python -m seed.query_users
"""

import asyncio
import os
import sys
import argparse
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv("../.env")
load_dotenv(".env")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.models.user import User
from app.models.admin_user import AdminUser
from app.models.restaurant import Restaurant

def normalize_db_url(url: str) -> str:
    """Normalize database URL for asyncpg and enforce SSL for external hosts."""
    if url.startswith("postgres://"):
        url = "postgresql" + url[8:]
    if not url.startswith("postgresql+asyncpg://"):
        if url.startswith("postgresql://"):
            url = "postgresql+asyncpg" + url[10:]
            
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # Enforce SSL for remote Render hosts
    if "render.com" in parsed.netloc and "ssl" not in query_params and "sslmode" not in query_params:
        query_params["ssl"] = ["require"]
        
    new_query = urlencode(query_params, doseq=True)
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))

async def query_users(db_url: str):
    normalized_url = normalize_db_url(db_url)
    parsed = urlparse(normalized_url)
    masked_host = parsed.netloc.split("@")[-1] if "@" in parsed.netloc else parsed.netloc

    print("=" * 80)
    print(f"Connecting to database at: {masked_host}")
    print("=" * 80)

    engine = create_async_engine(normalized_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            # 1. Fetch Admin / Staff Users
            print("\n--- [ADMIN & STAFF USERS] (admin_users table) ---")
            admin_res = await session.execute(
                select(AdminUser, Restaurant.name.label("restaurant_name"))
                .outerjoin(Restaurant, AdminUser.restaurant_id == Restaurant.id)
                .order_by(AdminUser.created_at.desc())
            )
            admin_rows = admin_res.all()

            if not admin_rows:
                print("No admin users found.")
            else:
                print(f"{'Email':<32} | {'Role':<18} | {'Assigned Venue':<25} | {'Active':<6}")
                print("-" * 88)
                for admin, rest_name in admin_rows:
                    venue = rest_name or "System-wide"
                    active_str = "Yes" if admin.is_active else "No"
                    print(f"{admin.email:<32} | {admin.role:<18} | {venue:<25} | {active_str:<6}")

            # 2. Fetch Customer Users
            print("\n--- [CUSTOMER USERS] (users table) ---")
            user_res = await session.execute(
                select(User).order_by(User.created_at.desc())
            )
            users = user_res.scalars().all()

            if not users:
                print("No customer users found.")
            else:
                print(f"{'Name':<24} | {'Email':<32} | {'User ID':<36}")
                print("-" * 96)
                for u in users:
                    name = u.name or "(Anonymous)"
                    email = u.email or "(None)"
                    print(f"{name:<24} | {email:<32} | {u.id:<36}")

            print("\n" + "=" * 80)
            print(f"Total: {len(admin_rows)} admin/staff users, {len(users)} customer users.")
            print("=" * 80 + "\n")

    finally:
        await engine.dispose()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query users and emails from database")
    parser.add_argument("--url", type=str, help="PostgreSQL connection string (Render External URL)", default="")
    args = parser.parse_args()

    db_url = args.url or os.environ.get("RENDER_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: No database URL provided. Pass --url='...' or set DATABASE_URL in environment.")
        sys.exit(1)

    asyncio.run(query_users(db_url))

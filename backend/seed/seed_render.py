"""
CLI Utility to safely truncate and reseed the Render production/staging PostgreSQL database.
Usage:
  python -m seed.seed_render --url="postgresql://user:password@host.render.com/dbname" --yes
  or
  $env:DATABASE_URL="postgresql://user:password@host.render.com/dbname"
  python -m seed.seed_render --yes
"""

import asyncio
import os
import sys
import argparse
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from seed.truncate_db import truncate
from seed.seed_data import seed

def normalize_render_url(url: str) -> str:
    """
    Normalizes Render PostgreSQL URL for SQLAlchemy asyncpg.
    Converts postgres:// or postgresql:// to postgresql+asyncpg://
    and ensures sslmode/ssl parameter is configured properly.
    """
    if url.startswith("postgres://"):
        url = "postgresql" + url[8:]
    if not url.startswith("postgresql+asyncpg://"):
        if url.startswith("postgresql://"):
            url = "postgresql+asyncpg" + url[10:]
            
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # Ensure SSL is enabled for Render external connections
    if "ssl" not in query_params and "sslmode" not in query_params:
        query_params["ssl"] = ["require"]
        
    new_query = urlencode(query_params, doseq=True)
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    return normalized

async def run_render_seed(db_url: str, auto_confirm: bool = False):
    normalized_url = normalize_render_url(db_url)
    parsed = urlparse(normalized_url)
    masked_host = parsed.netloc.split("@")[-1] if "@" in parsed.netloc else parsed.netloc
    
    print("=" * 60)
    print("SmartDiner - Render Database Seeding Utility")
    print("=" * 60)
    print(f"Target Database Host: {masked_host}")
    print(f"Target Database Path: {parsed.path}")
    print("-" * 60)
    
    if not auto_confirm:
        confirm = input("WARNING: This will TRUNCATE and RE-SEED all tables on Render. Continue? (y/N): ").strip().lower()
        if confirm != "y":
            print("Operation aborted by user.")
            return

    print("Connecting to Render PostgreSQL via asyncpg...")
    engine = create_async_engine(
        normalized_url,
        echo=False,
        pool_pre_ping=True
    )
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )
    
    try:
        await truncate(session_factory=session_factory)
        await seed(session_factory=session_factory)
        print("=" * 60)
        print("Render database seeded successfully with 6 restaurants and diverse menus.")
        print("=" * 60)
    finally:
        await engine.dispose()

def main():
    parser = argparse.ArgumentParser(description="Seed Render external database")
    parser.add_argument("--url", type=str, help="Render external PostgreSQL connection string", default="")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()
    
    db_url = args.url or os.environ.get("RENDER_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: No database URL provided. Pass --url='postgresql://...' or set DATABASE_URL.")
        sys.exit(1)
        
    asyncio.run(run_render_seed(db_url, auto_confirm=args.yes))

if __name__ == "__main__":
    main()

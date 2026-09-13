import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(settings.database_url)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    async_session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

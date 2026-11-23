import os

from functools import cache

from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
load_dotenv()

# HOW TO USE SESSION FACTORY
# - To use CRUD function you need to do:
"""
factory = get_session_factory()
async with factory() as session:
    await create_user(...)  
"""
#
@cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    url = os.getenv("DATABASE_URL")

    if not url:
        raise RuntimeError("DATABASE_URL is not configured")

    parsed = make_url(url)

    if parsed.drivername in {"postgres", "postgresql"}:
        parsed = parsed.set(drivername="postgresql+asyncpg")

    if parsed.drivername != "postgresql+asyncpg":
        raise ValueError("Expected PostgreSQL with asyncpg")

    engine = create_async_engine(
        parsed,
        pool_pre_ping=True,
    )

    return async_sessionmaker(
        engine,
        expire_on_commit=False,
    )
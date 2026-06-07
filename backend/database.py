import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Use pool URL in production (Azure), direct URL locally
DATABASE_URL = (
    os.getenv("DATABASE_POOL_URL")      # set in Azure Container Apps env vars
    or os.getenv("DATABASE_URL")        # fallback for local dev
)

engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,          # Session pooler supports up to 15 — 5 is safe
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,    # recycle connections every 30min
    echo=False
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
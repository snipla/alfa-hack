import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.shared.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def database_lifespan() -> AsyncGenerator[dict[str, Any]]:
    engine = create_async_engine(
        str(settings.DATABASE_URL),
        pool_pre_ping=True,
        pool_recycle=1800,
        echo=False,
    )
    session_maker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    logger.info("Database session was started")

    try:
        yield {"db_sessionmaker": session_maker}
    finally:
        await engine.dispose()

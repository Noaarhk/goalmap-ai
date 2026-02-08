from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.core.config import settings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# SQLAlchemy Async Engine
engine = create_async_engine(
    settings.ASYNC_DATABASE_URI,
    echo=False,
    connect_args={"prepared_statement_cache_size": 0},
    pool_pre_ping=True,
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a database session.
    """
    async with async_session_factory() as session:
        yield session


@asynccontextmanager
async def get_postgres_saver():
    """
    Yields an AsyncPostgresSaver connected to the DB.
    Handles the connection pool lifecycle.
    """
    # Use the connection string directly or construct it
    # psycopg uses a slightly different format than sqlalchemy, but standard libpq works
    conn_string = settings.SQLALCHEMY_DATABASE_URI

    async with AsyncConnectionPool(
        conn_string, max_size=20, kwargs={"autocommit": True}
    ) as pool:
        saver = AsyncPostgresSaver(pool)
        # We need to setup the tables first if they don't exist
        await saver.setup()
        yield saver

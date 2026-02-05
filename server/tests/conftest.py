from typing import AsyncGenerator

import asyncpg
import pytest
from app.core.config import settings
from app.models.base import Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Define Test Database Name and URL
TEST_DB_NAME = "goalmap_test"
TEST_DB_URL = settings.ASYNC_DATABASE_URI.replace(
    f"/{settings.POSTGRES_DB}", f"/{TEST_DB_NAME}"
)


@pytest.fixture(scope="function", autouse=True)
async def setup_test_db():
    """
    Session-scoped fixture to create/drop the test database.
    Connects to 'postgres' system db to perform admin operations.
    """
    # Using asyncpg directly for admin tasks (CREATE/DROP DATABASE)
    # Connect to the default 'postgres' database to perform admin commands
    sys_conn = await asyncpg.connect(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_SERVER,
        port=settings.POSTGRES_PORT,
        database="postgres",
    )

    try:
        # Drop if exists
        await sys_conn.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"')
        # Create
        await sys_conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await sys_conn.close()

    yield

    # Teardown: Drop DB
    sys_conn = await asyncpg.connect(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_SERVER,
        port=settings.POSTGRES_PORT,
        database="postgres",
    )
    try:
        # Terminate all connections to test db before dropping
        await sys_conn.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{TEST_DB_NAME}'
            AND pid <> pg_backend_pid();
        """)
        await sys_conn.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"')
    finally:
        await sys_conn.close()


@pytest.fixture(scope="function")
async def engine(setup_test_db):
    """
    Function-scoped engine that connects to the test DB.
    Creates tables before test, drops them after.
    Using NullPool to avoid connection holding issues during DB drop.
    """
    # Use the Test DB URL
    engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session

"""
Root conftest.py - Shared test utilities only.

DB-specific fixtures are in tests/integration/conftest.py
"""

from app.core.uow import AsyncUnitOfWork
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.roadmap_repo import RoadmapRepository
from sqlalchemy.ext.asyncio import AsyncSession


# =============================================================================
# Test Unit of Work (Reusable across all tests)
# =============================================================================


class TestUnitOfWork(AsyncUnitOfWork):
    """
    Test-specific UoW that accepts an existing session.
    Use this instead of duplicating the class in every test file.
    """

    def __init__(self, session: AsyncSession):
        super().__init__()
        self.session = session

    async def __aenter__(self):
        self.conversations = ConversationRepository(self.session)
        self.roadmaps = RoadmapRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        else:
            await self.session.flush()

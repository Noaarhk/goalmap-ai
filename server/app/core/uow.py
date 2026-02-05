from typing import TYPE_CHECKING

from app.core.database import async_session_factory

if TYPE_CHECKING:
    from app.repositories.conversation_repo import ConversationRepository
    from app.repositories.roadmap_repo import RoadmapRepository
    from sqlalchemy.ext.asyncio import AsyncSession


class AsyncUnitOfWork:
    """
    Manages a single database session and coordinates multiple repositories.
    Ensures atomic transactions across all repository operations.
    """

    def __init__(self):
        self._session_factory = async_session_factory
        self.session: "AsyncSession" | None = None

        # Repositories
        self.conversations: "ConversationRepository" | None = None
        self.roadmaps: "RoadmapRepository" | None = None

    async def __aenter__(self):
        self.session = self._session_factory()

        # Initialize repositories with the shared session
        from app.repositories.conversation_repo import ConversationRepository
        from app.repositories.roadmap_repo import RoadmapRepository

        self.conversations = ConversationRepository(self.session)
        self.roadmaps = RoadmapRepository(self.session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type:
                await self.rollback()
            else:
                await self.commit()
            await self.session.close()

    async def commit(self):
        if self.session:
            await self.session.commit()

    async def rollback(self):
        if self.session:
            await self.session.rollback()

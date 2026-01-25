from app.models.roadmap import Roadmap
from app.repositories.base import BaseRepository
from sqlalchemy import select


class RoadmapRepository(BaseRepository[Roadmap]):
    def __init__(self, db):
        super().__init__(Roadmap, db)

    async def get_by_user_id(self, user_id: str) -> list[Roadmap]:
        query = (
            select(Roadmap)
            .where(Roadmap.user_id == user_id)
            .order_by(Roadmap.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

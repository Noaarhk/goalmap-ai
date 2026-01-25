from typing import Any
from uuid import UUID

from app.models.conversation import Conversation
from app.repositories.base import BaseRepository
from sqlalchemy import select


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, db):
        super().__init__(Conversation, db)

    async def get_by_user_id(self, user_id: str) -> list[Conversation]:
        query = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def append_message(
        self, conversation_id: UUID, message: dict[str, Any]
    ) -> Conversation | None:
        conversation = await self.get(conversation_id)
        if conversation:
            # SQLAlchemy mutable JSON workaround or re-assignment
            # We must create a new list for it to detect change if using specific drivers,
            # but JSONB usually requires re-assignment of the field generally.
            new_messages = list(conversation.messages)
            new_messages.append(message)
            conversation.messages = new_messages
            await self.db.commit()
            await self.db.refresh(conversation)
        return conversation

    async def update_blueprint(
        self, conversation_id: UUID, blueprint: dict[str, Any]
    ) -> Conversation | None:
        conversation = await self.get(conversation_id)
        if conversation:
            conversation.blueprint = blueprint
            await self.db.commit()
            await self.db.refresh(conversation)
        return conversation

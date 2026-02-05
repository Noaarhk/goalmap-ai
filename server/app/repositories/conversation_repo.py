from typing import Any
from uuid import UUID

from app.models.blueprint import Blueprint
from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.base import BaseRepository
from sqlalchemy import inspect, select
from sqlalchemy.orm import selectinload


def _get_blueprint_columns() -> set[str]:
    """Get updatable columns from Blueprint model dynamically."""
    mapper = inspect(Blueprint)
    excluded = {"id", "conversation_id", "created_at", "updated_at"}
    return {c.key for c in mapper.columns if c.key not in excluded}


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, db):
        super().__init__(Conversation, db)

    def _load_relations(self, query):
        return query.options(
            selectinload(Conversation.messages),
            selectinload(Conversation.blueprint),
        )

    async def get_by_user_with_messages_and_blueprint(
        self, user_id: str
    ) -> list[Conversation]:
        query = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        query = self._load_relations(query)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_with_messages_and_blueprint(self, id: UUID) -> Conversation | None:
        query = select(Conversation).where(Conversation.id == id)
        query = self._load_relations(query)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Conversation:
        conversation = Conversation(**kwargs)
        self.db.add(conversation)
        await self.db.flush()
        # No refresh here, re-fetch will do it if needed, or rely on UoW commit
        res = await self.get_with_messages_and_blueprint(conversation.id)
        if not res:
            raise Exception("Conversation created but not found")
        return res

    async def update(self, db_obj: Conversation, **kwargs) -> Conversation:
        for key, value in kwargs.items():
            setattr(db_obj, key, value)
        await self.db.flush()
        # Re-fetch to restore relationships
        res = await self.get_with_messages_and_blueprint(db_obj.id)
        if not res:
            raise Exception("Conversation updated but not found")
        return res

    async def append_message(
        self, conversation_id: UUID, role: str, content: str
    ) -> Conversation | None:
        conversation = await self.get_with_messages_and_blueprint(conversation_id)
        if conversation:
            new_order = len(conversation.messages)
            new_message = Message(
                conversation_id=conversation_id,
                role=role,
                content=str(content),  # Ensure string
                order=new_order,
            )
            self.db.add(new_message)
            await self.db.flush()
            # Re-fetch to ensure order and relationships are correct for response
            return await self.get_with_messages_and_blueprint(conversation_id)
        return conversation

    async def update_blueprint(
        self, conversation_id: UUID, blueprint_data: dict[str, Any]
    ) -> Conversation | None:
        conversation = await self.get_with_messages_and_blueprint(conversation_id)
        if conversation:
            valid_columns = _get_blueprint_columns()
            mapped_data = {
                k: v for k, v in blueprint_data.items() if k in valid_columns
            }

            if conversation.blueprint:
                # Update existing
                for key, value in mapped_data.items():
                    if hasattr(conversation.blueprint, key):
                        setattr(conversation.blueprint, key, value)
            else:
                # Create new
                new_blueprint = Blueprint(
                    conversation_id=conversation_id, **mapped_data
                )
                self.db.add(new_blueprint)
                conversation.blueprint = new_blueprint

            await self.db.flush()
            # Re-fetch is vital here too
            return await self.get_with_messages_and_blueprint(conversation_id)
        return conversation

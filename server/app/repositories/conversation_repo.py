from typing import Any
from uuid import UUID

from app.models.blueprint import Blueprint
from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.base import BaseRepository
from sqlalchemy import select
from sqlalchemy.orm import selectinload


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
        await self.db.commit()
        await self.db.refresh(conversation)
        # Re-fetch with eager loads to satisfy response model
        res = await self.get_with_messages_and_blueprint(conversation.id)
        if not res:
            raise Exception("Conversation created but not found")
        return res

    async def update(self, db_obj: Conversation, **kwargs) -> Conversation:
        for key, value in kwargs.items():
            setattr(db_obj, key, value)
        await self.db.commit()
        await self.db.refresh(db_obj)
        # Re-fetch to restore relationships that might be expired by refresh
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
            await self.db.commit()
            await self.db.refresh(conversation)
            # Re-fetch to ensure order and relationships are correct for response
            return await self.get_with_messages_and_blueprint(conversation_id)
        return conversation

    async def update_blueprint(
        self, conversation_id: UUID, blueprint_data: dict[str, Any]
    ) -> Conversation | None:
        conversation = await self.get_with_messages_and_blueprint(conversation_id)
        if conversation:
            # Valid DB columns for blueprint
            valid_columns = {
                "start_point",
                "end_point",
                "motivations",
                "milestones",
                "field_scores",
                "timeline",
                "obstacles",
                "resources",
            }
            mapped_data = {}

            # 1. Direct Field Mapping (snake_case only)
            for k, v in blueprint_data.items():
                if k in valid_columns:
                    mapped_data[k] = v

            # 2. Semantic Mapping (Agent Output -> DB Model)
            # 'goal' from Agent -> 'end_point' in DB
            if "goal" in blueprint_data and "end_point" not in mapped_data:
                mapped_data["end_point"] = blueprint_data["goal"]

            # 'why' from Agent -> 'motivations' list in DB
            if "why" in blueprint_data and "motivations" not in mapped_data:
                why_text = blueprint_data["why"]
                mapped_data["motivations"] = [why_text] if why_text else []

            # 3. Direct Mapping for Context Fields
            if "timeline" in blueprint_data:
                mapped_data["timeline"] = blueprint_data["timeline"]
            if "obstacles" in blueprint_data:
                mapped_data["obstacles"] = blueprint_data["obstacles"]
            if "resources" in blueprint_data:
                mapped_data["resources"] = blueprint_data["resources"]

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

            await self.db.commit()
            await self.db.refresh(conversation)
            # Re-fetch is vital here too
            return await self.get_with_messages_and_blueprint(conversation_id)
        return conversation

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    title: str | None = None
    initial_message: str | None = None


class ConversationUpdate(BaseModel):
    title: str | None = None
    blueprint: dict | None = None


class ConversationResponse(BaseModel):
    id: UUID
    title: str | None
    messages: list[dict]
    blueprint: dict | None
    created_at: datetime
    updated_at: datetime


class RoadmapCreate(BaseModel):
    title: str
    goal: str
    milestones: list[dict]
    conversation_id: UUID | None = None


class RoadmapUpdate(BaseModel):
    title: str | None = None
    milestones: list[dict] | None = None


class RoadmapResponse(BaseModel):
    id: UUID
    title: str
    goal: str
    milestones: list[dict]
    created_at: datetime
    updated_at: datetime

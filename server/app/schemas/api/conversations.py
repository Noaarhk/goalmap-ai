from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    title: str | None = None
    initial_message: str | None = None


class ConversationUpdate(BaseModel):
    title: str | None = None
    blueprint: dict | None = None


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    order: int
    created_at: datetime


class BlueprintResponse(BaseModel):
    id: UUID
    start_point: str | None
    goal: str | None
    why: str | None

    # Context fields
    timeline: str | None = None
    obstacles: str | None = None
    resources: str | None = None

    milestones: list[str] = []
    field_scores: dict = {}
    created_at: datetime
    updated_at: datetime


class ConversationResponse(BaseModel):
    id: UUID
    title: str | None
    messages: list[MessageResponse] = []
    blueprint: BlueprintResponse | None = None
    created_at: datetime
    updated_at: datetime

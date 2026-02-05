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
    end_point: str | None
    motivations: list[str] = []

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


class RoadmapCreate(BaseModel):
    title: str
    goal: str
    milestones: list[dict]
    conversation_id: UUID | None = None


class RoadmapUpdate(BaseModel):
    title: str | None = None
    milestones: list[dict] | None = None


class NodeResponse(BaseModel):
    id: UUID
    parent_id: UUID | None
    type: str  # goal, milestone, task
    label: str
    details: str | None
    order: int
    is_assumed: bool
    status: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    duration_days: int | None = None
    created_at: datetime
    updated_at: datetime


class RoadmapResponse(BaseModel):
    id: UUID
    title: str
    goal: str
    status: str
    nodes: list[NodeResponse]
    created_at: datetime
    updated_at: datetime

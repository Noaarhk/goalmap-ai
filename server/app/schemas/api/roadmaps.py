from datetime import datetime
from uuid import UUID

from app.models.node import NodeStatus
from app.models.roadmap import RoadmapStatus
from pydantic import BaseModel


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
    status: NodeStatus
    start_date: datetime | None = None
    end_date: datetime | None = None
    duration_days: int | None = None
    created_at: datetime
    updated_at: datetime


class RoadmapResponse(BaseModel):
    id: UUID
    title: str
    goal: str
    status: RoadmapStatus
    nodes: list[NodeResponse]
    created_at: datetime
    updated_at: datetime


class GenerateRoadmapRequest(BaseModel):
    conversation_id: str
    goal: str
    why: str
    timeline: str | None = None
    obstacles: str | None = None
    resources: str | None = None

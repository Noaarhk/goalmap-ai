from datetime import date, datetime
from uuid import UUID

from app.models.node import NodeStatus
from app.models.roadmap import RoadmapStatus
from pydantic import BaseModel, ConfigDict


class RoadmapCreate(BaseModel):
    title: str
    goal: str
    milestones: list[dict]
    conversation_id: UUID | None = None


class RoadmapUpdate(BaseModel):
    title: str | None = None
    milestones: list[dict] | None = None


class NodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_id: UUID | None
    type: str  # goal, milestone, task
    label: str
    details: str | None
    order: int
    is_assumed: bool
    status: NodeStatus
    progress: int = 0
    completion_criteria: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    duration_days: int | None = None
    created_at: datetime
    updated_at: datetime


class RoadmapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    why: str | None = None
    timeline: str | None = None
    obstacles: str | None = None
    resources: str | None = None


class ModifiedMilestone(BaseModel):
    """User-modified milestone from the review screen."""

    id: str
    label: str
    details: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    completion_criteria: str | None = None
    is_new: bool = False  # True if user added this milestone


class ResumeRoadmapRequest(BaseModel):
    """Request to resume roadmap generation after skeleton approval."""

    roadmap_id: str  # DB roadmap UUID
    conversation_id: str | None = None

    # User modifications from review screen
    modified_milestones: list[ModifiedMilestone] | None = None

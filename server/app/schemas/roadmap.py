from typing import List, Optional

from pydantic import BaseModel, Field

# --- Domain Models ---


class Task(BaseModel):
    id: str
    label: str
    type: str = "task"  # "task", "milestone"
    status: str = "pending"
    details: Optional[str] = None


class Milestone(BaseModel):
    id: str
    label: str
    type: str = "milestone"
    tasks: List[Task] = Field(default_factory=list)
    order: int
    is_assumed: bool = False
    details: Optional[str] = None


class Roadmap(BaseModel):
    title: str
    milestones: List[Milestone] = Field(default_factory=list)


# --- SSE Event Models ---


class RoadmapMilestonesEvent(BaseModel):
    """Event sent when milestones (skeleton) are planned"""

    milestones: List[Milestone]


class RoadmapTasksEvent(BaseModel):
    """Event sent when tasks for a specific milestone are generated"""

    milestone_id: str
    tasks: List[Task]


# --- API Request Models ---


class GenerateRoadmapRequest(BaseModel):
    goal: str
    why: str
    timeline: str
    obstacles: Optional[str] = None
    resources: Optional[str] = None

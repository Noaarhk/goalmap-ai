from pydantic import BaseModel, Field

# --- Domain Models ---


class Task(BaseModel):
    id: str
    label: str
    type: str = "task"  # "task", "milestone"
    status: str = "pending"
    details: str | None = None


class Milestone(BaseModel):
    id: str
    label: str
    type: str = "milestone"
    tasks: list[Task] = Field(default_factory=list)
    order: int
    is_assumed: bool = False
    details: str | None = None


class Roadmap(BaseModel):
    title: str
    milestones: list[Milestone] = Field(default_factory=list)


# --- SSE Event Models ---


class RoadmapMilestonesEvent(BaseModel):
    """Event sent when milestones (skeleton) are planned"""

    milestones: list[Milestone]


class RoadmapTasksEvent(BaseModel):
    """Event sent when tasks for a specific milestone are generated"""

    milestone_id: str
    tasks: list[Task]


# --- API Request Models ---


class GenerateRoadmapRequest(BaseModel):
    goal: str
    why: str
    timeline: str | None = None
    obstacles: str | None = None
    resources: str | None = None

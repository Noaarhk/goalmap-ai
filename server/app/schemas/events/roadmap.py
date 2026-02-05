from app.models.node import NodeStatus
from pydantic import BaseModel, Field

# --- Storage/Transfer Types (with ID) ---


class BaseNode(BaseModel):
    """Base model for all roadmap nodes with ID."""

    id: str
    label: str
    type: str
    details: str | None = None
    status: NodeStatus = NodeStatus.PENDING
    order: int = 0
    is_assumed: bool = False
    # Enhanced fields
    progress: int = 0  # 0-100
    start_date: str | None = None  # YYYY-MM-DD
    end_date: str | None = None  # YYYY-MM-DD
    completion_criteria: str | None = None
    parent_id: str | None = None


class ActionNode(BaseNode):
    """Action item node."""

    type: str = "action"


class Milestone(BaseNode):
    """Milestone node containing actions."""

    type: str = "milestone"
    actions: list[ActionNode] = Field(default_factory=list)


class GoalNode(BaseNode):
    """Goal node containing milestones and direct actions."""

    type: str = "goal"
    milestones: list[Milestone] = Field(default_factory=list)
    actions: list[ActionNode] = Field(default_factory=list)


class Roadmap(BaseModel):
    """Complete roadmap with hierarchical goal structure."""

    title: str
    goal: GoalNode


# --- SSE Event Models ---


class RoadmapSkeletonEvent(BaseModel):
    """Event sent when skeleton (goal + milestones) is planned."""

    goal: GoalNode  # Contains milestones (actions empty)
    thread_id: str | None = None  # For HIL resume


class RoadmapActionsEvent(BaseModel):
    """Event sent when actions are generated."""

    milestone_id: str | None  # None = direct goal actions
    actions: list[ActionNode]


class RoadmapCompleteEvent(BaseModel):
    """Event sent when roadmap generation and persistence is complete."""

    roadmap_id: str  # Server-side UUID for the roadmap

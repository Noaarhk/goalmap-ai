from uuid import uuid4

from pydantic import BaseModel, Field

# --- LLM Output Types (no ID) ---


class ActionContent(BaseModel):
    """LLM output for action item."""

    label: str
    details: str | None = None
    is_assumed: bool = False


class MilestoneContent(BaseModel):
    """LLM output for milestone."""

    label: str
    details: str | None = None
    is_assumed: bool = False
    actions: list[ActionContent] = Field(default_factory=list)


class GoalContent(BaseModel):
    """LLM output for goal structure."""

    label: str
    details: str | None = None
    milestones: list[MilestoneContent] = Field(default_factory=list)
    actions: list[ActionContent] = Field(default_factory=list)  # Direct actions


# --- Storage/Transfer Types (with ID) ---


class BaseNode(BaseModel):
    """Base model for all roadmap nodes with ID."""

    id: str
    label: str
    type: str
    details: str | None = None
    status: str = "pending"  # pending, in_progress, completed
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


# --- ID Assignment Utilities ---


def assign_action_ids(actions: list[ActionContent], prefix: str) -> list[ActionNode]:
    """Assign UUIDs to action contents."""
    return [
        ActionNode(
            id=f"{prefix}-{str(uuid4())[:8]}",
            label=a.label,
            details=a.details,
            is_assumed=a.is_assumed,
            order=i,
        )
        for i, a in enumerate(actions)
    ]


def assign_milestone_ids(milestones: list[MilestoneContent]) -> list[Milestone]:
    """Assign UUIDs to milestone contents and their actions."""
    result = []
    for i, ms in enumerate(milestones):
        ms_id = f"ms-{str(uuid4())[:8]}"
        result.append(
            Milestone(
                id=ms_id,
                label=ms.label,
                details=ms.details,
                is_assumed=ms.is_assumed,
                order=i,
                actions=assign_action_ids(ms.actions, ms_id),
            )
        )
    return result


def assign_goal_ids(goal: GoalContent) -> GoalNode:
    """Assign UUIDs to goal content and all children."""
    goal_id = f"goal-{str(uuid4())[:8]}"
    return GoalNode(
        id=goal_id,
        label=goal.label,
        details=goal.details,
        milestones=assign_milestone_ids(goal.milestones),
        actions=assign_action_ids(goal.actions, goal_id),
    )


# --- SSE Event Models ---


class RoadmapSkeletonEvent(BaseModel):
    """Event sent when skeleton (goal + milestones) is planned."""

    goal: GoalNode  # Contains milestones (actions empty)


class RoadmapActionsEvent(BaseModel):
    """Event sent when actions for a specific milestone are generated."""

    milestone_id: str
    actions: list[ActionNode]


class RoadmapDirectActionsEvent(BaseModel):
    """Event sent when direct actions for the goal are generated."""

    actions: list[ActionNode]


# --- API Request Models ---


class GenerateRoadmapRequest(BaseModel):
    conversation_id: str
    goal: str
    why: str
    timeline: str | None = None
    obstacles: str | None = None
    resources: str | None = None

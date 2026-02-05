from typing import TypedDict

from app.schemas.events.roadmap import GoalNode


class RoadmapState(TypedDict):
    """
    State for the Roadmap Generation Agent.

    Attributes:
        context: All input context (goal, why, timeline, obstacles, resources).
        goal_node: The complete hierarchical goal structure with IDs assigned.
    """

    # Input context from discovery
    context: dict  # {"goal": "...", "why": "...", "timeline": "...", ...}
    # Output - hierarchical goal structure (contains milestones and actions)
    goal_node: GoalNode | None

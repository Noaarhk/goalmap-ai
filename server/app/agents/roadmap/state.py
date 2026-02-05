"""
DEPRECATED: Roadmap no longer uses LangGraph state.
This module is kept for backward compatibility.
"""

import warnings
from typing import Literal, TypedDict

from app.schemas.events.roadmap import GoalNode

warnings.warn(
    "app.agents.roadmap.state is deprecated. Roadmap now uses plain async functions.",
    DeprecationWarning,
    stacklevel=2,
)


class RoadmapState(TypedDict):
    """Deprecated state type."""

    context: dict
    goal_node: GoalNode | None
    status: Literal["pending", "skeleton_ready", "approved", "completed"] | None

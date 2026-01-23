import operator
from typing import Annotated, List, TypedDict

from app.schemas.roadmap import Milestone


class RoadmapState(TypedDict):
    """
    State for the Roadmap Generation Agent.

    Attributes:
        goal: The goal to generate the roadmap for.
        context: Additional context like why, timeline, etc.
        milestones: The list of milestones generated so far.
    """

    goal: str
    context: dict
    # We allow milestones to be appended to
    milestones: Annotated[List[Milestone], operator.add]

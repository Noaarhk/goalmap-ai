from typing import Annotated, Any, List, Optional, TypedDict

from app.schemas.discovery import BlueprintData
from langgraph.graph.message import add_messages


class DiscoveryState(TypedDict):
    """
    State for the Goal Discovery Agent.

    Attributes:
        messages: The conversation history (including current user message).
        blueprint: The current state of the goal blueprint.
        user_intent: Analysis of what the user wants to do (e.g. 'refine_goal', 'just_chat').
        next_step: The next node to execute determined by the router.
    """

    messages: Annotated[List[Any], add_messages]
    blueprint: BlueprintData
    user_intent: Optional[str]
    analysis_status: str  # For UI feedback e.g. "analyzing"

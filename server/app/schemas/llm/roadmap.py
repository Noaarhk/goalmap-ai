from pydantic import BaseModel, Field


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

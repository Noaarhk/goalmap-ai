from pydantic import BaseModel


class BlueprintUpdateEventData(BaseModel):
    """Partial update for the blueprint"""

    goal: str | None = None
    why: str | None = None
    timeline: str | None = None
    obstacles: str | None = None
    resources: str | None = None
    milestones: list[str] | None = None
    field_scores: dict[str, int] | None = None
    readiness_tips: list[str] | None = None
    success_tips: list[str] | None = None
    uncertainties: list[dict] | None = None

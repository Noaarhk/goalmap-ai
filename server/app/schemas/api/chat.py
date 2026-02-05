from pydantic import BaseModel, Field


class FieldScores(BaseModel):
    goal: int = 0
    why: int = 0
    timeline: int = 0
    obstacles: int = 0
    resources: int = 0
    milestones: int = 0


class BlueprintData(BaseModel):
    goal: str | None = None
    why: str | None = None
    timeline: str | None = None
    obstacles: str | None = None
    resources: str | None = None
    milestones: list[str] = Field(default_factory=list)
    field_scores: FieldScores = Field(default_factory=FieldScores)
    readiness_tips: list[str] = Field(default_factory=list)
    success_tips: list[str] = Field(default_factory=list)
    uncertainties: list[dict] = Field(default_factory=list)


class ChatRequest(BaseModel):
    chat_id: str | None = None
    message: str
    history: list[dict[str, str]] = []  # [{"role": "user", "content": "..."}]
    current_blueprint: BlueprintData | None = None

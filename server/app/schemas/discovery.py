from pydantic import BaseModel, Field

# --- Domain Models ---


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
    fieldScores: FieldScores = Field(default_factory=FieldScores)
    readinessTips: list[str] = Field(default_factory=list)
    successTips: list[str] = Field(default_factory=list)


# --- SSE Event Models ---


class TokenEventData(BaseModel):
    text: str
    run_id: str | None = None


class StatusEventData(BaseModel):
    message: str
    node: str


class BlueprintUpdateEventData(BaseModel):
    """Partial update for the blueprint"""

    goal: str | None = None
    why: str | None = None
    timeline: str | None = None
    obstacles: str | None = None
    resources: str | None = None
    milestones: list[str] | None = None
    fieldScores: dict[str, int] | None = None
    readinessTips: list[str] | None = None
    successTips: list[str] | None = None


class ErrorEventData(BaseModel):
    code: str
    message: str


# --- API Request Models ---


class ChatRequest(BaseModel):
    chat_id: str | None = None
    message: str
    history: list[dict[str, str]] = []  # [{"role": "user", "content": "..."}]
    current_blueprint: BlueprintData | None = None

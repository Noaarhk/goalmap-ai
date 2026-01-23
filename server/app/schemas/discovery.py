from typing import Dict, List, Optional

from pydantic import BaseModel, Field

# --- Domain Models ---


class FieldScores(BaseModel):
    goal: int = 0
    why: int = 0
    timeline: int = 0
    obstacles: int = 0
    resources: int = 0


class BlueprintData(BaseModel):
    goal: Optional[str] = None
    why: Optional[str] = None
    timeline: Optional[str] = None
    obstacles: Optional[str] = None
    resources: Optional[str] = None
    fieldScores: FieldScores = Field(default_factory=FieldScores)
    readinessTips: List[str] = Field(default_factory=list)
    successTips: List[str] = Field(default_factory=list)


# --- SSE Event Models ---


class TokenEventData(BaseModel):
    text: str
    run_id: Optional[str] = None


class StatusEventData(BaseModel):
    message: str
    node: str


class BlueprintUpdateEventData(BaseModel):
    """Partial update for the blueprint"""

    goal: Optional[str] = None
    why: Optional[str] = None
    timeline: Optional[str] = None
    obstacles: Optional[str] = None
    resources: Optional[str] = None
    fieldScores: Optional[Dict[str, int]] = None
    readinessTips: Optional[List[str]] = None
    successTips: Optional[List[str]] = None


class ErrorEventData(BaseModel):
    code: str
    message: str


# --- API Request Models ---


class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []  # [{"role": "user", "content": "..."}]
    current_blueprint: Optional[BlueprintData] = None

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NodeUpdate(BaseModel):
    """A single node progress update proposed by the AI."""

    node_id: UUID
    progress_delta: int  # How much to increase progress (0-100)
    log_entry: str  # History entry explaining what was done


class CheckInAnalyzeRequest(BaseModel):
    """Request to analyze a user's check-in text."""

    roadmap_id: UUID
    user_input: str


class CheckInAnalyzeResponse(BaseModel):
    """Response with proposed updates from AI analysis."""

    checkin_id: UUID
    proposed_updates: list[NodeUpdate]


class CheckInConfirmRequest(BaseModel):
    """Request to confirm/apply the proposed updates."""

    checkin_id: UUID
    updates: list[NodeUpdate] | None = None  # Optional: modified updates from frontend


class CheckInConfirmResponse(BaseModel):
    """Response after confirming updates."""

    success: bool
    updated_nodes: list[UUID]


class CheckInResponse(BaseModel):
    """Full check-in record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    roadmap_id: UUID
    user_input: str
    proposed_updates: list[dict]
    confirmed_updates: list[dict] | None
    status: str  # pending, confirmed, rejected
    created_at: datetime

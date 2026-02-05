from uuid import UUID

from app.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class Blueprint(Base):
    __tablename__ = "blueprints"

    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), unique=True
    )
    start_point: Mapped[str | None] = mapped_column(nullable=True)
    end_point: Mapped[str | None] = mapped_column(nullable=True)

    # Context fields
    timeline: Mapped[str | None] = mapped_column(nullable=True)
    obstacles: Mapped[str | None] = mapped_column(nullable=True)
    resources: Mapped[str | None] = mapped_column(nullable=True)

    # Stored as lists of strings
    motivations: Mapped[list[str]] = mapped_column(JSONB, default=list)
    milestones: Mapped[list[str]] = mapped_column(JSONB, default=list)

    # New Field: Uncertainties
    # Structure: [{"text": "timeline is vague", "type": "timeline", "count": 1}]
    uncertainties: Mapped[list[dict]] = mapped_column(JSONB, default=list)

    # Stored as dictionary
    field_scores: Mapped[dict] = mapped_column(JSONB, default=dict)

    def __repr__(self) -> str:
        return f"<Blueprint id={self.id} conversation_id={self.conversation_id}>"

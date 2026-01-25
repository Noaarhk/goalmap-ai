from uuid import UUID

from app.models.base import Base
from app.models.conversation import Conversation
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Roadmap(Base):
    __tablename__ = "roadmaps"

    user_id: Mapped[str] = mapped_column(index=True)
    conversation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column()
    goal: Mapped[str] = mapped_column()

    # Store milestones as JSONB: [{id, label, tasks: [...]}]
    # We could normalize this further (Roadmap -> Milestone -> Task),
    # but for this app, storing the whole roadmap structure as JSON is often more convenient
    # given its document-like nature and the fact that we often load/save the whole thing.
    milestones: Mapped[list[dict]] = mapped_column(JSONB, default=list)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="roadmaps")

    def __repr__(self) -> str:
        return f"<Roadmap id={self.id} title={self.title} user_id={self.user_id}>"

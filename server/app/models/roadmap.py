from typing import TYPE_CHECKING
from uuid import UUID

from app.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.checkin import CheckIn
    from app.models.conversation import Conversation
    from app.models.node import Node


class Roadmap(Base):
    __tablename__ = "roadmaps"

    user_id: Mapped[str] = mapped_column(index=True)
    conversation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, unique=True
    )

    title: Mapped[str] = mapped_column()
    goal: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column(
        default="draft"
    )  # draft, active, completed, archived

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="roadmap")
    nodes: Mapped[list["Node"]] = relationship(
        "Node",
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="Node.order",
    )
    checkins: Mapped[list["CheckIn"]] = relationship(
        "CheckIn", back_populates="roadmap", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Roadmap id={self.id} title={self.title} user_id={self.user_id}>"

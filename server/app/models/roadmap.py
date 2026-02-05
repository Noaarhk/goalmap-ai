from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from app.models.base import Base
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.checkin import CheckIn
    from app.models.conversation import Conversation
    from app.models.node import Node


class RoadmapStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Roadmap(Base):
    __tablename__ = "roadmaps"

    user_id: Mapped[str] = mapped_column(index=True)
    conversation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, unique=True
    )

    title: Mapped[str] = mapped_column()
    goal: Mapped[str] = mapped_column()
    status: Mapped[RoadmapStatus] = mapped_column(
        SQLEnum(RoadmapStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=RoadmapStatus.DRAFT,
    )

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

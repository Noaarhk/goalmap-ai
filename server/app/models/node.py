from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from app.models.base import Base
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.roadmap import Roadmap


from enum import Enum


class NodeType(str, Enum):
    GOAL = "goal"
    MILESTONE = "milestone"
    ACTION = "action"
    TASK = "task"  # Deprecated, use ACTION


class NodeStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Node(Base):
    __tablename__ = "nodes"

    roadmap_id: Mapped[UUID] = mapped_column(
        ForeignKey("roadmaps.id", ondelete="CASCADE"), index=True
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("nodes.id", ondelete="CASCADE"), nullable=True
    )

    type: Mapped[NodeType] = mapped_column(
        SQLEnum(NodeType, values_callable=lambda obj: [e.name.upper() for e in obj])
    )
    label: Mapped[str] = mapped_column()
    details: Mapped[str | None] = mapped_column(nullable=True)
    order: Mapped[int] = mapped_column(default=0)

    is_assumed: Mapped[bool] = mapped_column(default=False)
    status: Mapped[NodeStatus] = mapped_column(
        SQLEnum(NodeStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=NodeStatus.PENDING,
    )

    # Period fields
    start_date: Mapped[date | None] = mapped_column(nullable=True)
    end_date: Mapped[date | None] = mapped_column(nullable=True)
    duration_days: Mapped[int | None] = mapped_column(
        nullable=True
    )  # Estimated duration in days

    # Progress tracking (0-100)
    progress: Mapped[int] = mapped_column(default=0)
    completion_criteria: Mapped[str | None] = mapped_column(nullable=True)

    # Relationships
    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="nodes")

    # Self-referential relationship for tree structure
    parent: Mapped["Node | None"] = relationship(
        "Node", remote_side="Node.id", back_populates="children"
    )
    children: Mapped[list["Node"]] = relationship(
        "Node", back_populates="parent", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Node id={self.id} label={self.label} type={self.type}>"

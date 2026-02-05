from typing import TYPE_CHECKING
from uuid import UUID

from app.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.roadmap import Roadmap


class CheckIn(Base):
    __tablename__ = "checkins"

    roadmap_id: Mapped[UUID] = mapped_column(
        ForeignKey("roadmaps.id", ondelete="CASCADE"), index=True
    )

    user_input: Mapped[str] = mapped_column()  # What the user said they did

    # AI proposed updates: list of dicts describing changes to nodes
    proposed_updates: Mapped[list[dict]] = mapped_column(JSONB, default=list)

    # Confirmed updates: what was actually applied (or null if pending)
    confirmed_updates: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[str] = mapped_column(
        default="pending"
    )  # pending, confirmed, rejected

    # Relationship
    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="checkins")

    def __repr__(self) -> str:
        return (
            f"<CheckIn id={self.id} roadmap_id={self.roadmap_id} status={self.status}>"
        )

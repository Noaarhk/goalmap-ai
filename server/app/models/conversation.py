from typing import TYPE_CHECKING

from app.models.base import Base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.roadmap import Roadmap


class Conversation(Base):
    __tablename__ = "conversations"

    user_id: Mapped[str] = mapped_column(index=True)  # From Supabase JWT
    title: Mapped[str | None] = mapped_column(nullable=True)

    # Store messages as a list of dicts: [{"role": "user", "content": "..."}]
    messages: Mapped[list[dict]] = mapped_column(JSONB, default=list)

    # Store current blueprint state
    blueprint: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    roadmaps: Mapped[list["Roadmap"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} user_id={self.user_id} title={self.title}>"

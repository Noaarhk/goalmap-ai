from typing import TYPE_CHECKING

from app.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.blueprint import Blueprint
    from app.models.message import Message
    from app.models.roadmap import Roadmap


class Conversation(Base):
    __tablename__ = "conversations"

    user_id: Mapped[str] = mapped_column(index=True)
    title: Mapped[str | None] = mapped_column(nullable=True)

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        backref="conversation",
        cascade="all, delete-orphan",
        order_by="Message.order",
    )
    blueprint: Mapped["Blueprint"] = relationship(
        "Blueprint", backref="conversation", uselist=False, cascade="all, delete-orphan"
    )
    roadmap: Mapped["Roadmap"] = relationship(
        "Roadmap",
        back_populates="conversation",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} user_id={self.user_id} title={self.title}>"

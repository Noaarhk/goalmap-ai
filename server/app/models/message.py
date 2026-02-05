from uuid import UUID

from app.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class Message(Base):
    __tablename__ = "messages"

    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column()  # "user" | "assistant" | "system"
    content: Mapped[str] = mapped_column()
    order: Mapped[int] = mapped_column()

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role} order={self.order}>"

from app.core.config import settings
from langfuse.callback import CallbackHandler


def get_langfuse_handler(
    user_id: str | None = None,
    session_id: str | None = None,
    tags: list[str] | None = None,
):
    """Returns Langfuse callback handler for LangChain integration."""
    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        return None

    return CallbackHandler(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST,
        user_id=user_id,
        session_id=session_id,
        tags=tags or [],
    )

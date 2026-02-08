import logging

from app.core.config import settings
from langchain_core.prompts import ChatPromptTemplate
from langfuse.callback import CallbackHandler

logger = logging.getLogger(__name__)


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


# Initialize Langfuse Client (Singleton)
langfuse_client = None
if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
    try:
        from langfuse import Langfuse

        langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
    except ImportError:
        pass

# Prompt cache: fetched once at startup, reused forever
_prompt_cache: dict[str, ChatPromptTemplate] = {}


def _fetch_prompt(name: str) -> ChatPromptTemplate | None:
    """Single Langfuse fetch attempt. Returns None on failure."""
    if not langfuse_client:
        return None
    try:
        prompt_client = langfuse_client.get_prompt(name, type="chat")
        logger.info(f"Loaded prompt '{name}' v{prompt_client.version} from Langfuse")
        prompt = prompt_client.get_langchain_prompt()

        if isinstance(prompt, ChatPromptTemplate):
            return prompt
        if isinstance(prompt, list):
            return ChatPromptTemplate.from_messages(prompt)
        logger.warning(f"Unexpected prompt type {type(prompt)} for '{name}'")
    except Exception as e:
        logger.warning(f"Failed to fetch prompt '{name}' from Langfuse: {e}")
    return None


def preload_prompts(prompt_names: list[str]) -> None:
    """Fetch all prompts from Langfuse at once (call at server startup)."""
    if not langfuse_client:
        logger.info("Langfuse not configured, using local fallbacks")
        return

    for name in prompt_names:
        result = _fetch_prompt(name)
        if result:
            _prompt_cache[name] = result

    logger.info(f"Preloaded {len(_prompt_cache)}/{len(prompt_names)} prompts from Langfuse")


def get_prompt(name: str, fallback: ChatPromptTemplate) -> ChatPromptTemplate:
    """Return cached prompt or fallback. No network calls after startup."""
    if name in _prompt_cache:
        logger.debug(f"Using Langfuse prompt for '{name}'")
        return _prompt_cache[name]
    logger.debug(f"Using local fallback prompt for '{name}'")
    return fallback

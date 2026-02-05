from app.core.config import settings
from langchain_core.prompts import ChatPromptTemplate
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


def get_prompt(name: str, fallback: str) -> ChatPromptTemplate:
    """
    Fetch a prompt from Langfuse.
    If fails or not configured, return a ChatPromptTemplate from the fallback string.
    """
    import logging

    from langchain_core.messages import SystemMessage
    # ChatPromptTemplate import moved to top

    logger = logging.getLogger(__name__)

    if langfuse_client:
        try:
            # Langfuse get_prompt returns a Langchain prompt template
            # type_ defined as "chat" in Langfuse allows pulling as ChatPrompt
            prompt_client = langfuse_client.get_prompt(name, type="chat")
            logger.info(
                f"Loaded prompt '{name}' version {prompt_client.version} from Langfuse"
            )
            prompt = prompt_client.get_langchain_prompt()

            # Defensive conversion: ensure ChatPromptTemplate type
            # External library may return list or other types in edge cases
            if isinstance(prompt, ChatPromptTemplate):
                return prompt
            elif isinstance(prompt, list):
                logger.warning(
                    f"Prompt '{name}' returned list, converting to ChatPromptTemplate"
                )
                return ChatPromptTemplate.from_messages(prompt)
            else:
                logger.warning(f"Unexpected prompt type {type(prompt)}, using fallback")
        except Exception as e:
            # Log error ideally
            logger.warning(f"Failed to fetch prompt '{name}' from Langfuse: {e}")

    # Fallback: Construct a simple ChatPromptTemplate
    # Assuming the fallback string is a System Prompt
    logger.info(f"Loaded prompt '{name}' from local fallback constants")
    return ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=fallback),
            ("human", "Latest: {last_message}\n\nHistory:\n{history}"),
        ]
    )

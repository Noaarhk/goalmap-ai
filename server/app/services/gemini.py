from functools import lru_cache

from app.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI


@lru_cache()
def get_llm(model: str = "gemini-1.5-flash"):
    """
    Returns a cached instance of the ChatGoogleGenerativeAI client.
    Ensures that we don't recreate the client on every request.
    """
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.7,
        convert_system_message_to_human=True,
    )

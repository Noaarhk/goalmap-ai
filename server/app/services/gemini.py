from functools import lru_cache

from app.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI


@lru_cache()
def get_llm(model: str = "gemini-3-flash-preview"):
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


def parse_gemini_output(ai_message):
    """
    Helper to extract text from Gemini's structured content (list of dicts).
    """
    content = ai_message.content
    if isinstance(content, list):
        return "".join([c["text"] for c in content if c.get("type") == "text"])
    return content

import os
import sys

# Add server directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.discovery.prompts import (
    FALLBACK_ANALYSIS_SYSTEM_PROMPT,
    FALLBACK_CHAT_SYSTEM_PROMPT,
)
from app.core.config import settings
from langfuse import Langfuse


def main():
    print("Syncing prompts to Langfuse...")

    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        print("Error: Langfuse credentials not found in env.")
        return

    langfuse = Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST,
    )

    # 1. Discovery Analysis Prompt
    print("Creating 'discovery-analysis'...")
    langfuse.create_prompt(
        name="discovery-analysis",
        prompt=[
            {"role": "system", "content": FALLBACK_ANALYSIS_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "Latest: {{last_message}}\n\nHistory:\n{{history}}",
            },
        ],
        type="chat",
        labels=["production"],
        config={
            "temperature": 0,
            "response_format": {"type": "json_object"},
        },
    )

    # 2. Discovery Chat Prompt
    print("Creating 'discovery-chat'...")
    langfuse.create_prompt(
        name="discovery-chat",
        prompt=[
            {"role": "system", "content": FALLBACK_CHAT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "Latest: {{last_message}}\n\nHistory:\n{{history}}",
            },
        ],
        type="chat",
        labels=["production"],
        config={
            "temperature": 0.7,
        },
    )

    print("Success! Prompts synced.")


if __name__ == "__main__":
    main()

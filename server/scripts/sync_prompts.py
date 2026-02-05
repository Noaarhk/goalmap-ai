"""
Sync prompts to Langfuse.

Usage:
    cd server && uv run python scripts/sync_prompts.py
"""

import os
import sys

# Add server directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.discovery.prompts import (
    FALLBACK_ANALYSIS_SYSTEM_PROMPT,
    FALLBACK_CHAT_SYSTEM_PROMPT,
)
from app.agents.roadmap.prompts import (
    ACTION_GENERATOR_PROMPT,
    DIRECT_ACTIONS_PROMPT,
    STRATEGIC_PLANNER_PROMPT,
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

    # --- Discovery Prompts ---

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

    # --- Roadmap Prompts ---

    print("Creating 'roadmap-skeleton'...")
    langfuse.create_prompt(
        name="roadmap-skeleton",
        prompt=[
            {"role": "system", "content": STRATEGIC_PLANNER_PROMPT},
            {"role": "user", "content": "Create the roadmap skeleton."},
        ],
        type="chat",
        labels=["production"],
        config={
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        },
    )

    print("Creating 'roadmap-actions'...")
    langfuse.create_prompt(
        name="roadmap-actions",
        prompt=[
            {"role": "system", "content": ACTION_GENERATOR_PROMPT},
            {"role": "user", "content": "Generate actions."},
        ],
        type="chat",
        labels=["production"],
        config={
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        },
    )

    print("Creating 'roadmap-direct-actions'...")
    langfuse.create_prompt(
        name="roadmap-direct-actions",
        prompt=[
            {"role": "system", "content": DIRECT_ACTIONS_PROMPT},
            {"role": "user", "content": "Generate direct goal actions."},
        ],
        type="chat",
        labels=["production"],
        config={
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        },
    )

    langfuse.flush()
    print("✅ Success! All prompts synced to Langfuse.")


if __name__ == "__main__":
    main()

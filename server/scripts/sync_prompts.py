"""
Sync local prompts to Langfuse.

Uploads all prompt templates so they can be versioned/edited in the Langfuse UI.
Prompt names here MUST match the names used in get_prompt() calls across the codebase.

Usage:
    cd server && uv run python scripts/sync_prompts.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.discovery.prompts import (
    _CHAT_SYSTEM_PROMPT,
    _PRE_ANALYSIS_SYSTEM_PROMPT,
)
from app.agents.roadmap.prompts import (
    _ACTION_GENERATOR_SYSTEM,
    _STRATEGIC_PLANNER_SYSTEM,
)
from app.core.config import settings
from app.services.checkin_service import FALLBACK_CHECKIN_ANALYSIS_PROMPT
from langfuse import Langfuse

# All prompts that the app uses, keyed by Langfuse name
PROMPTS = {
    "discovery-chat": {
        "messages": [
            {"role": "system", "content": _CHAT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "Latest: {{last_message}}\n\nHistory:\n{{history}}",
            },
        ],
        "config": {"temperature": 0.7},
    },
    "discovery-analysis": {
        "messages": [
            {"role": "system", "content": _PRE_ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": "Analyze and return JSON only."},
        ],
        "config": {"temperature": 0, "response_format": {"type": "json_object"}},
    },
    "roadmap-planner": {
        "messages": [
            {"role": "system", "content": _STRATEGIC_PLANNER_SYSTEM},
            {"role": "user", "content": "Create the roadmap skeleton."},
        ],
        "config": {"temperature": 0.3, "response_format": {"type": "json_object"}},
    },
    "roadmap-actions": {
        "messages": [
            {"role": "system", "content": _ACTION_GENERATOR_SYSTEM},
            {"role": "user", "content": "Generate actions."},
        ],
        "config": {"temperature": 0.3, "response_format": {"type": "json_object"}},
    },
    "checkin-analysis": {
        "messages": [
            {"role": "system", "content": FALLBACK_CHECKIN_ANALYSIS_PROMPT},
            {
                "role": "user",
                "content": 'User\'s check-in: "{{user_input}}"\n\nAvailable nodes:\n{{node_context}}\n\nAnalyze and return JSON with updates.',
            },
        ],
        "config": {"temperature": 0, "response_format": {"type": "json_object"}},
    },
}

# Old prompt names that are no longer used
DEPRECATED_PROMPTS = [
    "roadmap-direct-actions",
    "roadmap-skeleton",  # was renamed to roadmap-planner
]


def main():
    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        print("Error: Langfuse credentials not found in env.")
        return

    langfuse = Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST,
    )

    # Upload current prompts
    for name, prompt_data in PROMPTS.items():
        print(f"  ↑ Uploading '{name}'...")
        langfuse.create_prompt(
            name=name,
            prompt=prompt_data["messages"],
            type="chat",
            labels=["production"],
            config=prompt_data["config"],
        )

    langfuse.flush()

    print(f"\n✅ Synced {len(PROMPTS)} prompts to Langfuse.")

    if DEPRECATED_PROMPTS:
        print("\n⚠️  These old prompts can be manually deleted from the Langfuse UI:")
        for name in DEPRECATED_PROMPTS:
            print(f"   - {name}")


if __name__ == "__main__":
    main()

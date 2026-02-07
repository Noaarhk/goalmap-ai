"""
Roadmap Prompts - Fallback prompts and Langfuse getters
"""

from app.services.langfuse import get_prompt
from langchain_core.prompts import ChatPromptTemplate

# ============================================
# Fallback Prompts (used when Langfuse unavailable)
# ============================================

# Strategic Planner Prompt - Generates goal structure (no IDs)
_STRATEGIC_PLANNER_SYSTEM = """You are a Strategic Planner creating a hierarchical goal structure.

Goal: {goal}
Context: {context}

Create a goal structure with 3-5 major milestones.

Return JSON (NO IDs - they will be assigned by the system):
{{
    "goal": {{
        "label": "{goal}",
        "details": "Main objective summary",
        "milestones": [
            {{
                "label": "Milestone Title",
                "details": "Brief description",
                "is_assumed": false,
                "actions": []
            }}
        ],
        "actions": []
    }}
}}
"""

_STRATEGIC_PLANNER_FALLBACK = ChatPromptTemplate.from_messages(
    [
        ("system", _STRATEGIC_PLANNER_SYSTEM),
        ("human", "Create the roadmap skeleton."),
    ]
)

# Action Generator Prompt - Generates actions for a milestone (no IDs)
_ACTION_GENERATOR_SYSTEM = """You are an Action Planner.
Generate 3-5 specific action items for the given milestone.

Goal: {goal}
Milestone: {milestone_label} ({milestone_details})

Return JSON (NO IDs):
{{
    "actions": [
        {{
            "label": "Action Item",
            "details": "Specific action description",
            "is_assumed": false
        }}
    ]
}}
"""

_ACTION_GENERATOR_FALLBACK = ChatPromptTemplate.from_messages(
    [
        ("system", _ACTION_GENERATOR_SYSTEM),
        ("human", "Generate actions."),
    ]
)

# Direct Actions Prompt - Generates cross-cutting actions (no IDs)
_DIRECT_ACTIONS_SYSTEM = """You are an Action Planner.
Generate 1-3 cross-cutting actions that apply to the entire goal (not specific to any milestone).

Goal: {goal}
Context: {context}

Examples: "Daily practice", "Track progress weekly", "Join community"

Return JSON (NO IDs):
{{
    "actions": [
        {{
            "label": "Cross-cutting Action",
            "details": "Action that supports the whole journey",
            "is_assumed": false
        }}
    ]
}}
"""

_DIRECT_ACTIONS_FALLBACK = ChatPromptTemplate.from_messages(
    [
        ("system", _DIRECT_ACTIONS_SYSTEM),
        ("human", "Generate direct goal actions."),
    ]
)


# ============================================
# Prompt Getters (Langfuse with fallback)
# ============================================


def get_strategic_planner_prompt() -> ChatPromptTemplate:
    """Get strategic planner prompt from Langfuse or fallback to local."""
    return get_prompt("roadmap-planner", _STRATEGIC_PLANNER_FALLBACK)


def get_action_generator_prompt() -> ChatPromptTemplate:
    """Get action generator prompt from Langfuse or fallback to local."""
    return get_prompt("roadmap-actions", _ACTION_GENERATOR_FALLBACK)


def get_direct_actions_prompt() -> ChatPromptTemplate:
    """Get direct actions prompt from Langfuse or fallback to local."""
    return get_prompt("roadmap-direct-actions", _DIRECT_ACTIONS_FALLBACK)

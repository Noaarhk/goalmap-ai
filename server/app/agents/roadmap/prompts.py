"""
Roadmap Prompts - Fallback prompts and Langfuse getters
"""

from app.services.langfuse import get_prompt
from langchain_core.prompts import ChatPromptTemplate

# ============================================
# Fallback Prompts (used when Langfuse unavailable)
# ============================================

_STRATEGIC_PLANNER_SYSTEM = """You are a Strategic Planner creating a hierarchical goal structure.

Goal: {goal}
Context: {context}

Create a goal structure with 3-5 major milestones.
If the goal benefits from cross-cutting actions (e.g. daily habits, progress tracking),
include them in the top-level "actions" array. Otherwise leave it empty.

Return JSON (NO IDs - they will be assigned by the system):
{{
    "goal": {{
        "label": "{goal}",
        "details": "Main objective summary",
        "milestones": [
            {{
                "label": "Milestone Title",
                "details": "Brief description",
                "is_assumed": false
            }}
        ],
        "actions": [
            {{
                "label": "Cross-cutting action (optional)",
                "details": "Only if truly needed",
                "is_assumed": false
            }}
        ]
    }}
}}
"""

_STRATEGIC_PLANNER_FALLBACK = ChatPromptTemplate.from_messages(
    [
        ("system", _STRATEGIC_PLANNER_SYSTEM),
        ("human", "Create the roadmap skeleton."),
    ]
)

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


# ============================================
# Prompt Getters (Langfuse with fallback)
# ============================================


def get_strategic_planner_prompt() -> ChatPromptTemplate:
    """Get strategic planner prompt from Langfuse or fallback to local."""
    return get_prompt("roadmap-planner", _STRATEGIC_PLANNER_FALLBACK)


def get_action_generator_prompt() -> ChatPromptTemplate:
    """Get action generator prompt from Langfuse or fallback to local."""
    return get_prompt("roadmap-actions", _ACTION_GENERATOR_FALLBACK)

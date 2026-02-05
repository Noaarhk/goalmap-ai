# Strategic Planner Prompt - Generates goal structure (no IDs)
STRATEGIC_PLANNER_PROMPT = """You are a Strategic Planner creating a hierarchical goal structure.

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

# Action Generator Prompt - Generates actions for a milestone (no IDs)
ACTION_GENERATOR_PROMPT = """You are an Action Planner.
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

# Direct Actions Prompt - Generates cross-cutting actions (no IDs)
DIRECT_ACTIONS_PROMPT = """You are an Action Planner.
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

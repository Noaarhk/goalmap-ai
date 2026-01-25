# Strategic Planner Prompt
STRATEGIC_PLANNER_PROMPT = """You are a Strategic Planner.
Break down the goal into 3-5 major sequential milestones.

Goal: {goal}
Context: {context}

Return JSON list of milestones:
{{
    "milestones": [
        {{ "id": "m1", "label": "Milestone Title", "is_assumed": false, "order": 1, "details": "Brief description" }}
    ]
}}
"""

# Tactical Task Manager Prompt
TACTICAL_TASK_MANAGER_PROMPT = """You are a Tactical Task Manager.
Generate 3-5 specific execution tasks for the given milestone.

Goal: {goal}
Milestone: {milestone_label} ({milestone_details})

Return JSON list of tasks:
{{
    "tasks": [
        {{ "id": "t1", "label": "Action Item", "type": "task", "status": "pending", "details": "..." }}
    ]
}}
"""

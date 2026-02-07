"""
Discovery Pipeline V3 - Response First, Background Analysis

Key improvements:
- V1: 2 LLM calls (analyze -> generate) = slow first token
- V2: 1 LLM call with JSON suffix = parsing complexity
- V3: 1 LLM call for response + background analysis = fast & clean

Flow:
1. stream_response() -> immediate token streaming
2. analyze_response_background() -> async analysis after completion
"""

import json
import re
from typing import AsyncGenerator

from app.schemas.api.chat import BlueprintData
from app.services.gemini import get_llm
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Greeting Instructions
GREETING_INSTRUCTION_FIRST_TURN = (
    "Start with a warm, brief Korean greeting since this is the first interaction."
)
GREETING_INSTRUCTION_DEFAULT = "DO NOT greet. Continue naturally."

# Simple chat prompt - no JSON output required
CHAT_SYSTEM_PROMPT = """You are 'QuestForge AI', a strategic Goal Coach & Pathfinder.

**Current Blueprint Status:**
- Goal: {current_goal} (Score: {goal_score}/100)
- Why: {current_why} (Score: {why_score}/100)
- Timeline: {timeline}
- Resources: {resources}
- Obstacles: {obstacles}
- Milestones: {milestones}
- Unresolved Uncertainties: {uncertainties}

**Response Strategy:**
1. If Goal is unclear (score < 70): Ask specific questions about what they want to achieve.
2. If Start is unclear: Ask about current situation, resources, or challenges.
3. If Uncertainties exist: Gently address them - ask to clarify or offer to proceed with assumptions.
4. If both are clear (> 80): Summarize and encourage roadmap generation.
5. When user asks for help: Provide 2-3 concrete options.

**Tone:** Professional yet witty. Speak Korean naturally.

{greeting_instruction}

Respond naturally. Do NOT output JSON or any structured data.
"""

CHAT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", CHAT_SYSTEM_PROMPT),
        ("human", "Latest: {last_message}\n\nHistory:\n{history}"),
    ]
)

# Background analysis prompt - runs after response is complete
ANALYSIS_SYSTEM_PROMPT = """You are an expert Goal Analyst. Analyze the conversation and extract information.

**Current Blueprint:**
- Goal: {current_goal}
- Why: {current_why}
- Timeline: {timeline}
- Obstacles: {obstacles}
- Resources: {resources}
- Existing Uncertainties: {uncertainties}

**Latest Exchange:**
User: {user_message}
Assistant: {assistant_response}

**Task:**
1. Extract any NEW information from this exchange.
2. Detect uncertainties - vague statements that need clarification later.

**Uncertainty Detection Rules:**
- Look for: "아마", "maybe", "잘 모르겠지만", "될 수도", "I'm not sure", "it depends", "probably"
- Also detect implicit uncertainty: vague timelines ("soon"), unclear metrics ("better"), ambiguous goals
- Example: "6개월 안에 하고 싶은데 바쁠 수도 있어요" -> {{"text": "일정이 바빠질 가능성", "type": "timeline", "resolved": false}}

**Scoring Guidelines (0-100):**
- 0-30: Vague information
- 31-60: Specific domain defined
- 61-80: Concrete details identified
- 81-100: Highly specific with deadlines/measurables

Return ONLY valid JSON:
{{
    "extracted": {{
        "goal": "new goal text or null",
        "why": "new why text or null",
        "timeline": "new timeline or null",
        "obstacles": "new obstacles or null",
        "resources": "new resources or null"
    }},
    "scores": {{
        "goal": 0-100,
        "why": 0-100,
        "timeline": 0-100,
        "obstacles": 0-100,
        "resources": 0-100
    }},
    "tips": ["improvement tip 1", "tip 2"],
    "uncertainties": [
        {{"text": "uncertainty description in Korean", "type": "timeline|resources|goal|obstacles|general", "resolved": false}}
    ]
}}
"""

ANALYSIS_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", ANALYSIS_SYSTEM_PROMPT),
        ("human", "Analyze and return JSON only."),
    ]
)

llm = get_llm()

__all__ = ["stream_response", "analyze_response_background"]


async def stream_response(
    messages: list[BaseMessage],
    blueprint: BlueprintData,
    callbacks: list | None = None,
) -> AsyncGenerator[str, None]:
    """
    Stream chat response immediately. No analysis blocking.

    Yields tokens as they're generated.
    """
    human_messages = [m for m in messages if m.type == "human"]
    is_first_turn = len(human_messages) <= 1
    last_message = messages[-1].content if messages else ""
    history_str = "\n".join([f"{m.type}: {m.content}" for m in messages[-6:]])

    greeting_instruction = (
        GREETING_INSTRUCTION_FIRST_TURN
        if is_first_turn
        else GREETING_INSTRUCTION_DEFAULT
    )

    # Format unresolved uncertainties
    unresolved_uncertainties = "None"
    if blueprint.uncertainties:
        unresolved = [
            u for u in blueprint.uncertainties if not u.get("resolved", False)
        ]
        if unresolved:
            unresolved_uncertainties = ", ".join(
                [
                    f"{u.get('text', '')} ({u.get('type', 'general')})"
                    for u in unresolved
                ]
            )

    prompt_variables = {
        "greeting_instruction": greeting_instruction,
        "current_goal": blueprint.goal or "Not set",
        "goal_score": blueprint.field_scores.goal,
        "current_why": blueprint.why or "Not set",
        "why_score": blueprint.field_scores.why,
        "timeline": blueprint.timeline or "Not set",
        "milestones": ", ".join(blueprint.milestones)
        if blueprint.milestones
        else "None",
        "obstacles": blueprint.obstacles or "None",
        "resources": blueprint.resources or "None",
        "uncertainties": unresolved_uncertainties,
        "last_message": last_message,
        "history": history_str,
    }

    chain = CHAT_PROMPT | llm | StrOutputParser()

    config = {"tags": ["stream_response_v3"]}
    if callbacks:
        config["callbacks"] = callbacks

    async for chunk in chain.astream(prompt_variables, config=config):
        if chunk:
            yield chunk


async def analyze_response_background(
    user_message: str,
    assistant_response: str,
    blueprint: BlueprintData,
    callbacks: list | None = None,
) -> BlueprintData:
    """
    Analyze the completed response in background.
    Called after streaming is complete.

    Returns updated blueprint.
    """
    # Format existing uncertainties for context
    existing_uncertainties = "None"
    if blueprint.uncertainties:
        existing_uncertainties = ", ".join(
            [
                f"{u.get('text', '')} ({u.get('type', 'general')})"
                for u in blueprint.uncertainties
            ]
        )

    prompt_variables = {
        "current_goal": blueprint.goal or "Not set",
        "current_why": blueprint.why or "Not set",
        "timeline": blueprint.timeline or "Not set",
        "obstacles": blueprint.obstacles or "None",
        "resources": blueprint.resources or "None",
        "uncertainties": existing_uncertainties,
        "user_message": user_message,
        "assistant_response": assistant_response,
    }

    chain = ANALYSIS_PROMPT | llm | StrOutputParser()

    config = {"tags": ["analyze_background_v3"]}
    if callbacks:
        config["callbacks"] = callbacks

    try:
        result_str = await chain.ainvoke(prompt_variables, config=config)

        # Parse JSON from response
        # Clean up potential markdown code blocks
        json_clean = re.sub(r"^```json?\s*", "", result_str.strip())
        json_clean = re.sub(r"\s*```$", "", json_clean)

        result = json.loads(json_clean)

        # Apply updates
        update_fields = {}

        extracted = result.get("extracted", {})
        for key in ["goal", "why", "timeline", "obstacles", "resources"]:
            if extracted.get(key) and extracted[key] != "null":
                update_fields[key] = extracted[key]

        if result.get("scores"):
            updated_scores = blueprint.field_scores.model_copy(update=result["scores"])
            update_fields["field_scores"] = updated_scores

        if result.get("tips"):
            update_fields["readiness_tips"] = result["tips"]

        # Handle uncertainties - merge new with existing, avoid duplicates
        if result.get("uncertainties"):
            new_uncertainties = result["uncertainties"]
            existing = blueprint.uncertainties or []

            # Get existing uncertainty texts for deduplication
            existing_texts = {u.get("text", "").lower() for u in existing}

            # Add new uncertainties that aren't duplicates
            merged = list(existing)
            for u in new_uncertainties:
                if u.get("text", "").lower() not in existing_texts:
                    # Ensure resolved field exists
                    if "resolved" not in u:
                        u["resolved"] = False
                    merged.append(u)

            update_fields["uncertainties"] = merged

        return (
            blueprint.model_copy(update=update_fields) if update_fields else blueprint
        )

    except Exception as e:
        print(f"[V3] Background analysis failed: {e}")
        return blueprint  # Return unchanged on failure

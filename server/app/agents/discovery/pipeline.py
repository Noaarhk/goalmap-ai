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

from app.agents.discovery.prompts import (
    GREETING_INSTRUCTION_DEFAULT,
    GREETING_INSTRUCTION_FIRST_TURN,
    get_analysis_prompt,
    get_chat_prompt,
)
from app.schemas.api.chat import BlueprintData
from app.services.gemini import get_llm
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser

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

    chat_prompt = get_chat_prompt()
    chain = chat_prompt | llm | StrOutputParser()

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

    analysis_prompt = get_analysis_prompt()
    chain = analysis_prompt | llm | StrOutputParser()

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

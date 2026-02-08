"""
Discovery Pipeline V4 - Analyze First, Then Respond

Key improvement over V3:
- V3: stream_response(old blueprint) -> analyze_background -> blueprint update
  Problem: AI doesn't know what to ask because blueprint isn't updated yet
- V4: analyze_user_message -> stream_response(updated blueprint) -> emit blueprint
  Fix: AI sees the UPDATED blueprint, so it knows exactly what's missing

Flow:
1. analyze_user_message() -> extract info from user's message, update blueprint
2. stream_response() -> stream tokens with UPDATED blueprint context
"""

import json
import logging
import re
from typing import AsyncGenerator

from app.agents.discovery.prompts import (
    GREETING_INSTRUCTION_DEFAULT,
    GREETING_INSTRUCTION_FIRST_TURN,
    get_chat_prompt,
    get_pre_analysis_prompt,
)
from app.schemas.api.chat import BlueprintData
from app.services.gemini import get_llm
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

llm = get_llm()

__all__ = ["analyze_user_message", "stream_response"]


async def analyze_user_message(
    user_message: str,
    history: list[BaseMessage],
    blueprint: BlueprintData,
    callbacks: list | None = None,
) -> BlueprintData:
    """
    Pre-analyze the user's message BEFORE generating a response.
    Updates the blueprint so the response generator knows what to ask next.
    """
    existing_uncertainties = "None"
    if blueprint.uncertainties:
        existing_uncertainties = ", ".join(
            [
                f"{u.get('text', '')} ({u.get('type', 'general')}, resolved={u.get('resolved', False)})"
                for u in blueprint.uncertainties
            ]
        )

    history_str = "\n".join([f"{m.type}: {m.content}" for m in history[-6:]])

    prompt_variables = {
        "current_goal": blueprint.goal or "Not set",
        "current_why": blueprint.why or "Not set",
        "timeline": blueprint.timeline or "Not set",
        "obstacles": blueprint.obstacles or "None",
        "resources": blueprint.resources or "None",
        "uncertainties": existing_uncertainties,
        "history": history_str,
        "user_message": user_message,
    }

    pre_analysis_prompt = get_pre_analysis_prompt()
    chain = pre_analysis_prompt | llm | StrOutputParser()

    config = {"tags": ["pre_analysis_v4"]}
    if callbacks:
        config["callbacks"] = callbacks

    try:
        result_str = await chain.ainvoke(prompt_variables, config=config)

        json_clean = re.sub(r"^```json?\s*", "", result_str.strip())
        json_clean = re.sub(r"\s*```$", "", json_clean)
        result = json.loads(json_clean)

        update_fields = {}

        # Extract new field values
        extracted = result.get("extracted", {})
        for key in ["goal", "why", "timeline", "obstacles", "resources"]:
            if extracted.get(key) and extracted[key] != "null":
                update_fields[key] = extracted[key]

        # Update scores
        if result.get("scores"):
            updated_scores = blueprint.field_scores.model_copy(update=result["scores"])
            update_fields["field_scores"] = updated_scores

        # Store tips
        if result.get("tips"):
            update_fields["readiness_tips"] = result["tips"]

        # Handle uncertainties - merge + resolve
        if result.get("uncertainties") is not None:
            new_uncertainties = result["uncertainties"]
            existing = blueprint.uncertainties or []

            existing_texts = {u.get("text", "").lower() for u in existing}

            merged = list(existing)
            for u in new_uncertainties:
                text_lower = u.get("text", "").lower()
                if text_lower not in existing_texts:
                    if "resolved" not in u:
                        u["resolved"] = False
                    merged.append(u)
                else:
                    # Update resolved status if the new one says resolved
                    if u.get("resolved", False):
                        for existing_u in merged:
                            if existing_u.get("text", "").lower() == text_lower:
                                existing_u["resolved"] = True

            update_fields["uncertainties"] = merged

        return (
            blueprint.model_copy(update=update_fields) if update_fields else blueprint
        )

    except Exception as e:
        logger.warning(f"Pre-analysis failed, proceeding with current blueprint: {e}")
        return blueprint


async def stream_response(
    messages: list[BaseMessage],
    blueprint: BlueprintData,
    missing_fields: list[str] | None = None,
    callbacks: list | None = None,
) -> AsyncGenerator[str, None]:
    """
    Stream chat response using the UPDATED blueprint.
    The blueprint has already been analyzed, so the AI knows what info is missing.
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

    # Format missing fields for the prompt
    missing_fields_str = ", ".join(missing_fields) if missing_fields else "None"

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
        "missing_fields": missing_fields_str,
        "last_message": last_message,
        "history": history_str,
    }

    chat_prompt = get_chat_prompt()
    chain = chat_prompt | llm | StrOutputParser()

    config = {"tags": ["stream_response_v4"]}
    if callbacks:
        config["callbacks"] = callbacks

    async for chunk in chain.astream(prompt_variables, config=config):
        if chunk:
            yield chunk

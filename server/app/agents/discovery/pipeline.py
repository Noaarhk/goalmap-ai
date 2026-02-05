"""
Discovery Pipeline - Simple async functions (no graph needed)

Flow: analyze_turn() -> generate_chat()
"""

from typing import Any, AsyncGenerator

from app.agents.discovery.prompts import (
    FALLBACK_ANALYSIS_SYSTEM_PROMPT,
    FALLBACK_CHAT_SYSTEM_PROMPT,
    GREETING_INSTRUCTION_DEFAULT,
    GREETING_INSTRUCTION_FIRST_TURN,
    SUGGESTION_INSTRUCTION,
)
from app.schemas.api.chat import BlueprintData
from app.services.gemini import get_llm, parse_gemini_output
from app.services.langfuse import get_prompt
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Fallback prompts as ChatPromptTemplates
FALLBACK_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", FALLBACK_ANALYSIS_SYSTEM_PROMPT),
        ("human", "Latest: {last_message}\n\nHistory:\n{history}"),
    ]
)

FALLBACK_CHAT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", FALLBACK_CHAT_SYSTEM_PROMPT),
        ("human", "Latest: {last_message}\n\nHistory:\n{history}"),
    ]
)

llm = get_llm()

__all__ = ["analyze_turn", "generate_chat_stream", "llm"]


async def analyze_turn(
    messages: list[BaseMessage],
    blueprint: BlueprintData,
) -> BlueprintData:
    """
    Step 1: Analyze user input and update blueprint.
    Returns updated blueprint (does NOT generate response).
    """
    last_message = messages[-1].content if messages else ""
    history_str = "\n".join([f"{m.type}: {m.content}" for m in messages[-6:]])

    prompt_variables = {
        "current_goal": blueprint.goal or "Not set",
        "goal_score": blueprint.field_scores.goal,
        "current_why": blueprint.why or "Not set",
        "why_score": blueprint.field_scores.why,
        "milestones": ", ".join(blueprint.milestones) if blueprint.milestones else "None",
        "obstacles": blueprint.obstacles or "None",
        "resources": blueprint.resources or "None",
        "last_message": last_message,
        "history": history_str,
    }

    prompt = get_prompt("discovery-analysis", fallback=FALLBACK_ANALYSIS_PROMPT)
    chain = prompt | llm | parse_gemini_output | JsonOutputParser()
    chain = chain.with_config(tags=["analyze_turn"])

    try:
        result = await chain.ainvoke(prompt_variables)

        # Build update dict from extracted fields
        extracted = result.get("extracted", {})
        update_fields = {k: v for k, v in extracted.items() if v is not None}

        if result.get("scores"):
            updated_scores = blueprint.field_scores.model_copy(update=result["scores"])
            update_fields["field_scores"] = updated_scores

        if result.get("tips"):
            update_fields["readiness_tips"] = result["tips"]

        if result.get("uncertainties"):
            update_fields["uncertainties"] = result["uncertainties"]

        return blueprint.model_copy(update=update_fields)

    except Exception as e:
        print(f"Analysis failed: {e}")
        return blueprint  # Return unchanged on failure


async def generate_chat_stream(
    messages: list[BaseMessage],
    blueprint: BlueprintData,
    callbacks: list | None = None,
) -> AsyncGenerator[str, None]:
    """
    Step 2: Generate response with token streaming.
    Yields tokens as they're generated.
    """
    human_messages = [m for m in messages if m.type == "human"]
    is_first_turn = len(human_messages) <= 1
    last_message = messages[-1].content if messages else ""
    history_str = "\n".join([f"{m.type}: {m.content}" for m in messages[-6:]])

    # Check for suggestion request
    is_asking_for_suggestions = any(
        keyword in last_message.lower()
        for keyword in ["제안", "추천", "도와", "알려", "예시", "suggest", "help"]
    )

    greeting_instruction = (
        GREETING_INSTRUCTION_FIRST_TURN if is_first_turn else GREETING_INSTRUCTION_DEFAULT
    )
    suggestion_instruction = SUGGESTION_INSTRUCTION if is_asking_for_suggestions else ""

    prompt_variables = {
        "greeting_instruction": greeting_instruction,
        "suggestion_instruction": suggestion_instruction,
        "current_goal": blueprint.goal or "Not set",
        "goal_score": blueprint.field_scores.goal,
        "current_why": blueprint.why or "Not set",
        "why_score": blueprint.field_scores.why,
        "milestones": ", ".join(blueprint.milestones) if blueprint.milestones else "None",
        "obstacles": blueprint.obstacles or "None",
        "resources": blueprint.resources or "None",
        "uncertainties": ", ".join([u["text"] for u in blueprint.uncertainties])
        if blueprint.uncertainties
        else "None",
        "last_message": last_message,
        "history": history_str,
    }

    prompt = get_prompt("discovery-chat", fallback=FALLBACK_CHAT_PROMPT)
    chain = prompt | llm | StrOutputParser()

    config = {"tags": ["generate_chat"]}
    if callbacks:
        config["callbacks"] = callbacks

    async for chunk in chain.astream(prompt_variables, config=config):
        if chunk:
            yield chunk

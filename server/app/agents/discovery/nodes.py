# --- Node: Pipeline Handler (2-Step Architecture) ---
from typing import Any

from app.agents.discovery.prompts import (
    FALLBACK_ANALYSIS_SYSTEM_PROMPT,
    FALLBACK_CHAT_SYSTEM_PROMPT,
    GREETING_INSTRUCTION_DEFAULT,
    GREETING_INSTRUCTION_FIRST_TURN,
    SUGGESTION_INSTRUCTION,
)
from app.agents.discovery.state import DiscoveryState
from app.services.gemini import get_llm, parse_gemini_output
from app.services.langfuse import get_prompt
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Build fallback ChatPromptTemplates
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


async def analyze_turn(state: DiscoveryState) -> dict[str, Any]:
    """
    Step 1: Analyzer
    Analyze the user's input and update the blueprint (Goals, Scores, etc.).
    Does NOT generate a conversational response.
    """
    messages = state["messages"]
    current_blueprint = state["blueprint"]

    # Context for Analysis
    last_message = messages[-1].content if messages else ""
    history_str = "\n".join([f"{m.type}: {m.content}" for m in messages[-6:]])

    # Prepare variables for the prompt
    prompt_variables = {
        "current_goal": current_blueprint.goal or "Not set",
        "goal_score": current_blueprint.field_scores.goal,
        "current_why": current_blueprint.why or "Not set",
        "why_score": current_blueprint.field_scores.why,
        "milestones": ", ".join(current_blueprint.milestones)
        if current_blueprint.milestones
        else "None",
        "obstacles": current_blueprint.obstacles or "None",
        "resources": current_blueprint.resources or "None",
        "last_message": last_message,
        "history": history_str,
    }

    # Fetch prompt from Langfuse or use fallback
    prompt = get_prompt("discovery-analysis", fallback=FALLBACK_ANALYSIS_PROMPT)

    # dedicated chain for analysis
    chain = prompt | llm | parse_gemini_output | JsonOutputParser()
    chain = chain.with_config(tags=["analyze_turn"])

    try:
        result = await chain.ainvoke(prompt_variables)

        # Build update dict from extracted fields (only non-None values)
        extracted = result.get("extracted", {})
        update_fields = {k: v for k, v in extracted.items() if v is not None}

        # Update field_scores if present
        if result.get("scores"):
            scores = result["scores"]
            updated_scores = current_blueprint.field_scores.model_copy(update=scores)
            update_fields["field_scores"] = updated_scores

        # Update tips if present
        if result.get("tips"):
            update_fields["readiness_tips"] = result["tips"]

        # Update uncertainties if present
        if result.get("uncertainties"):
            update_fields["uncertainties"] = result["uncertainties"]

        # Create updated blueprint in one call
        updated_blueprint = current_blueprint.model_copy(update=update_fields)

        return {"blueprint": updated_blueprint}

    except Exception as e:
        print(f"Analysis failed: {e}")
        return {}  # No state update on failure


async def generate_chat(state: DiscoveryState) -> dict[str, Any]:
    """
    Step 2: Generator (Pathfinder)
    Generate a strategic response based on the UPDATED blueprint.
    This node streams the text response.
    """
    messages = state["messages"]
    current_blueprint = state["blueprint"]

    # Turn counting & Context
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
        GREETING_INSTRUCTION_FIRST_TURN
        if is_first_turn
        else GREETING_INSTRUCTION_DEFAULT
    )
    suggestion_instruction = SUGGESTION_INSTRUCTION if is_asking_for_suggestions else ""

    # Pathfinder Prompt with UPDATED Context
    # Prepare variables for the prompt
    prompt_variables = {
        "greeting_instruction": greeting_instruction,
        "suggestion_instruction": suggestion_instruction,
        "current_goal": current_blueprint.goal or "Not set",
        "goal_score": current_blueprint.field_scores.goal,
        "current_why": current_blueprint.why or "Not set",
        "why_score": current_blueprint.field_scores.why,
        "milestones": ", ".join(current_blueprint.milestones)
        if current_blueprint.milestones
        else "None",
        "obstacles": current_blueprint.obstacles or "None",
        "resources": current_blueprint.resources or "None",
        "uncertainties": ", ".join([u["text"] for u in current_blueprint.uncertainties])
        if current_blueprint.uncertainties
        else "None",
        "last_message": last_message,
        "history": history_str,
    }

    # Fetch prompt from Langfuse or use fallback
    prompt = get_prompt("discovery-chat", fallback=FALLBACK_CHAT_PROMPT)

    # Chain for generating response string
    chain = prompt | llm | StrOutputParser()
    chain = chain.with_config(tags=["generate_chat"])

    response_text = await chain.ainvoke(prompt_variables)

    return {"messages": [AIMessage(content=response_text)]}

# --- Node: Pipeline Handler (2-Step Architecture) ---
from typing import Any

from app.agents.discovery.prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    CHAT_SYSTEM_PROMPT,
    GREETING_INSTRUCTION_DEFAULT,
    GREETING_INSTRUCTION_FIRST_TURN,
    SUGGESTION_INSTRUCTION,
)
from app.agents.discovery.state import DiscoveryState
from app.services.gemini import get_llm, parse_gemini_output
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

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

    system_prompt = ANALYSIS_SYSTEM_PROMPT.format(
        current_goal=current_blueprint.goal or "Not set",
        goal_score=current_blueprint.fieldScores.goal,
        current_why=current_blueprint.why or "Not set",
        why_score=current_blueprint.fieldScores.why,
        milestones=", ".join(current_blueprint.milestones)
        if current_blueprint.milestones
        else "None",
        obstacles=current_blueprint.obstacles or "None",
        resources=current_blueprint.resources or "None",
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            ("human", "Latest: {last_message}\n\nHistory:\n{history}"),
        ]
    )

    # dedicated chain for analysis
    chain = prompt | llm | parse_gemini_output | JsonOutputParser()
    chain = chain.with_config(tags=["analyze_turn"])

    try:
        result = await chain.ainvoke(
            {
                "last_message": last_message,
                "history": history_str,
            }
        )

        # Update blueprint with extracted data
        updated_blueprint = current_blueprint.model_copy()

        if result.get("extracted"):
            extracted = result["extracted"]
            if extracted.get("goal"):
                updated_blueprint.goal = extracted["goal"]
            if extracted.get("why"):
                updated_blueprint.why = extracted["why"]
            if extracted.get("timeline"):
                updated_blueprint.timeline = extracted["timeline"]
            if extracted.get("obstacles"):
                updated_blueprint.obstacles = extracted["obstacles"]
            if extracted.get("resources"):
                updated_blueprint.resources = extracted["resources"]

        if result.get("scores"):
            scores = result["scores"]
            updated_blueprint.fieldScores.goal = scores.get("goal", 0)
            updated_blueprint.fieldScores.why = scores.get("why", 0)
            updated_blueprint.fieldScores.timeline = scores.get("timeline", 0)
            updated_blueprint.fieldScores.obstacles = scores.get("obstacles", 0)
            updated_blueprint.fieldScores.resources = scores.get("resources", 0)
            updated_blueprint.fieldScores.milestones = scores.get("milestones", 0)

        if result.get("tips"):
            updated_blueprint.readinessTips = result["tips"]

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
    system_prompt = CHAT_SYSTEM_PROMPT.format(
        greeting_instruction=greeting_instruction,
        suggestion_instruction=suggestion_instruction,
        current_goal=current_blueprint.goal or "Not set",
        goal_score=current_blueprint.fieldScores.goal,
        current_why=current_blueprint.why or "Not set",
        why_score=current_blueprint.fieldScores.why,
        milestones=", ".join(current_blueprint.milestones)
        if current_blueprint.milestones
        else "None",
        obstacles=current_blueprint.obstacles or "None",
        resources=current_blueprint.resources or "None",
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            ("human", "Latest: {last_message}\n\nHistory:\n{history}"),
        ]
    )

    # Chain for generating response string
    chain = prompt | llm | StrOutputParser()
    chain = chain.with_config(tags=["generate_chat"])

    response_text = await chain.ainvoke(
        {
            "last_message": last_message,
            "history": history_str,
        }
    )

    return {"messages": [AIMessage(content=response_text)]}

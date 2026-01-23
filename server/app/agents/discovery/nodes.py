from typing import Any, Dict

from app.agents.discovery.state import DiscoveryState
from app.services.gemini import get_llm
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

llm = get_llm()


# --- Node: Analyze Input ---
async def analyze_input(state: DiscoveryState) -> Dict[str, Any]:
    """
    Analyzes the user's latest message to determine intent and missing information.
    """
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an intent classifier for a goal setting AI.
        Analyze the user's latest message and current blueprint state.
        Determine if the user is:
        1. "greeting": Just saying hello/goodbye.
        2. "providing_info": Providing goal details (what, why, how).
        3. "asking_question": Asking for help or clarification.
        4. "chit_chat": Irrelevant conversation.
        
        Return JSON: {{ "intent": "SCREEN_KEY" }}
        Keys: greeting, providing_info, asking_question, chit_chat
        """,
            ),
            ("human", "{input}"),
        ]
    )

    chain = prompt | llm | JsonOutputParser()
    try:
        result = await chain.ainvoke({"input": last_message})
        return {
            "user_intent": result.get("intent", "providing_info"),
            "analysis_status": "analyzing_intent",
        }
    except Exception:
        return {"user_intent": "providing_info", "analysis_status": "error_analyzing"}


# --- Node: Extract Goal ---
async def extract_goal(state: DiscoveryState) -> Dict[str, Any]:
    """
    Extracts or refines the 'goal' and 'why' fields.
    """
    messages = state["messages"]
    current_blueprint = state["blueprint"]

    # Simple history string
    history_str = "\n".join([f"{m.type}: {m.content}" for m in messages[-10:]])

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a Goal Extractor.
        Extract 'goal' (main objective) and 'why' (motivation) from the conversation.
        If a field is already filled in the 'Current Blueprint', ONLY update it if the user explicitly changed it.
        Assign a confidence score (0-100) for each field.
        
        Current Blueprint:
        {current_blueprint}
        
        Return JSON:
        {{
            "goal": "string or null",
            "why": "string or null",
            "fieldScores": {{ "goal": int, "why": int }}
        }}
        """,
            ),
            ("human", "Conversation History:\n{history}"),
        ]
    )

    chain = prompt | llm | JsonOutputParser()
    try:
        result = await chain.ainvoke(
            {
                "current_blueprint": current_blueprint.model_dump_json(),
                "history": history_str,
            }
        )

        # Merge with existing data
        updated_blueprint = current_blueprint.model_copy()
        if result.get("goal"):
            updated_blueprint.goal = result["goal"]
        if result.get("why"):
            updated_blueprint.why = result["why"]

        if result.get("fieldScores"):
            updated_blueprint.fieldScores.goal = result["fieldScores"].get("goal", 0)
            updated_blueprint.fieldScores.why = result["fieldScores"].get("why", 0)

        return {"blueprint": updated_blueprint, "analysis_status": "extracted_goal"}
    except Exception as e:
        print(f"Goal extraction error: {e}")
        return {"analysis_status": "error_extracting_goal"}


# --- Node: Extract Tactics ---
async def extract_tactics(state: DiscoveryState) -> Dict[str, Any]:
    """
    Extracts timeline, obstacles, and resources.
    """
    messages = state["messages"]
    current_blueprint = state["blueprint"]
    history_str = "\n".join([f"{m.type}: {m.content}" for m in messages[-10:]])

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a Tactics Extractor.
        Extract 'timeline', 'obstacles', and 'resources' from the dialogue.
        Update based on new info.
        
        Current Blueprint:
        {current_blueprint}
        
        Return JSON with fieldScores.
        """,
            ),
            ("human", "Conversation History:\n{history}"),
        ]
    )

    chain = prompt | llm | JsonOutputParser()
    try:
        result = await chain.ainvoke(
            {
                "current_blueprint": current_blueprint.model_dump_json(),
                "history": history_str,
            }
        )

        updated_blueprint = current_blueprint.model_copy()
        for field in ["timeline", "obstacles", "resources"]:
            if result.get(field):
                setattr(updated_blueprint, field, result[field])

        if result.get("fieldScores"):
            scores = result["fieldScores"]
            updated_blueprint.fieldScores.timeline = scores.get("timeline", 0)
            updated_blueprint.fieldScores.obstacles = scores.get("obstacles", 0)
            updated_blueprint.fieldScores.resources = scores.get("resources", 0)

        return {"blueprint": updated_blueprint, "analysis_status": "extracted_tactics"}
    except Exception as e:
        print(f"Tactics extraction error: {e}")
        return {"analysis_status": "error_extracting_tactics"}


# --- Node: Generate Response ---
async def generate_response(state: DiscoveryState) -> Dict[str, Any]:
    """
    Generates a conversational response to the user.
    """
    messages = state["messages"]
    current_blueprint = state["blueprint"]
    # Intent could be used to customize greeting, but currently unused
    # intent = state.get("user_intent", "providing_info")

    system_prompt = """You are 'QuestForge AI', a witty and encouraging Goal Coach.
    Your goal is to help the user complete their Goal Blueprint.
    
    Current Blueprint Status:
    Goal: {goal} (Score: {goal_score})
    Why: {why} (Score: {why_score})
    Timeline: {timeline}
    
    Strategy:
    1. If information is missing, ask for it specifically (one thing at a time).
    2. If the user greets, greet back warmly.
    3. Be concise but inspiring.
    """

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", "{last_message}")]
    )

    chain = prompt | llm

    # Note: In a real streaming scenario, we would stream this generation.
    # For the graph node return, we just return the object. The streaming to client
    # happens via callbacks or by streaming the graph execution events.

    response = await chain.ainvoke(
        {
            "goal": current_blueprint.goal or "Unknown",
            "goal_score": current_blueprint.fieldScores.goal,
            "why": current_blueprint.why or "Unknown",
            "why_score": current_blueprint.fieldScores.why,
            "timeline": current_blueprint.timeline or "Unknown",
            "last_message": messages[-1].content,
        }
    )

    return {"messages": [response], "analysis_status": "responded"}


# --- Node: Construct Blueprint (Aggregator) ---
# Actually, the state update is preserved in the graph memory,
# so 'blueprint' key in state is already the latest.
# This node might be redundant if we just output the state,
# but useful for final formatting if needed.

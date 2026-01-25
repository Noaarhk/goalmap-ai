import asyncio
import os
import sys
import time

# Add server directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.discovery.graph import discovery_graph
from app.schemas.discovery import BlueprintData
from langchain_core.messages import HumanMessage


async def run_perf_test():
    print("🚀 Starting Performance Test for Discovery Agent (Pipeline v3)...")

    # Initial State
    initial_state = {
        "messages": [
            HumanMessage(
                content="나 유튜버 되고 싶은데, 지금 가진 건 아이폰 하나뿐이고 편집은 할 줄 몰라"
            )
        ],
        "blueprint": BlueprintData(),
        "user_intent": None,
        "analysis_status": "starting",
    }

    start_total = time.time()

    print("\n--- Step 1: Analysis & Extraction ---")
    start_analysis = time.time()

    # We use ainvoke for simplicity in testing, though the real app streams
    # The graph is sequential: analyze_turn -> generate_chat
    result = await discovery_graph.ainvoke(initial_state)

    end_total = time.time()

    # Extract results
    updated_blueprint = result["blueprint"]
    ai_messages = [m for m in result["messages"] if m.type == "ai"]
    last_response = ai_messages[-1].content if ai_messages else "No response"

    print(f"✅ Total Latency: {end_total - start_total:.2f}s")

    print("\n[Extraction Result]")
    print(f"Goal Score: {updated_blueprint.fieldScores.goal}")
    print(f"Obstacles: {updated_blueprint.obstacles}")
    print(f"Obstacles Score: {updated_blueprint.fieldScores.obstacles}")

    print("\n[AI Response]")
    print(last_response[:200] + "..." if len(last_response) > 200 else last_response)

    print("\n-------------------------------------------")
    if updated_blueprint.fieldScores.goal > 0 and "아이폰" in (
        updated_blueprint.resources or ""
    ):
        print("SUCCESS: Logic verified.")
    else:
        # Note: Resources extraction depends on the prompt, it might put it in obstacles or resources.
        # '아이폰 하나뿐' -> Resource: iPhone, Obstacle: editing skill
        print(f"Resources Found: {updated_blueprint.resources}")
        pass


if __name__ == "__main__":
    asyncio.run(run_perf_test())

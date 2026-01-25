import asyncio

from app.agents.discovery.nodes import llm
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate


async def test():
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                'You are an intent classifier. Return JSON: {{ "intent": "providing_info" }}',
            ),
            ("human", "My goal is to learn python"),
        ]
    )
    chain = prompt | llm

    print("--- Invoking Model ---")
    msg = await chain.ainvoke({})
    print(f"Raw Output Type: {type(msg.content)}")
    print(f"Raw Output: {msg.content}")

    # Fix logic
    content = msg.content
    if isinstance(content, list):
        print("Detected list content, extracting text...")
        content = "".join([c["text"] for c in content if c.get("type") == "text"])

    print(f"Extracted Content: {content}")

    try:
        parsed = JsonOutputParser().parse(content)
        print(f"Parsed JSON: {parsed}")
    except Exception as e:
        print(f"Parsing Error: {e}")


if __name__ == "__main__":
    asyncio.run(test())

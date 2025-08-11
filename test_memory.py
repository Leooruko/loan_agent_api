import asyncio
import re
from typing import Any, Dict

from langchain.agents import initialize_agent, AgentType

from utils_simple import (
    conversation_memory,
    tools,
    llm,
    get_conversation_memory,
    clear_conversation_memory,
)


def extract_output(response: Any) -> str:
    if isinstance(response, dict):
        return response.get("output", str(response))
    return str(response)


async def run_turns(agent, turns):
    outputs = []
    for prompt in turns:
        resp = agent.invoke({"input": prompt})
        outputs.append(extract_output(resp))
    return outputs


async def test_agent_memory(agent_name: str, agent):
    print(f"\n=== Testing memory for {agent_name} ===")
    clear_conversation_memory()

    turns = [
        "Note for this session: FAVORITE_CODE=ZX-42. Acknowledge only.",
        "What is FAVORITE_CODE I just told you? Answer with the code only.",
    ]

    outputs = await run_turns(agent, turns)
    for i, (inp, out) in enumerate(zip(turns, outputs), start=1):
        print(f"\nTurn {i} Input:\n{inp}\n")
        print(f"Turn {i} Output:\n{out}\n")

    mem = get_conversation_memory() or []
    print(f"Memory message count: {len(mem)}")
    if mem:
        print("Last 4 memory messages (most recent last):")
        for m in mem[-4:]:
            role = getattr(m, 'type', getattr(m, 'role', 'message'))
            content = getattr(m, 'content', '')
            print(f"- {role}: {content[:200]}{'...' if len(content) > 200 else ''}")


async def main():
    # ZERO_SHOT agent (may not leverage chat history effectively)
    zero_shot_agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=50,
        memory=conversation_memory,
        early_stopping_method="generate",
    )

    # CONVERSATIONAL agent (designed to include chat history in the prompt)
    conversational_agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=50,
        memory=conversation_memory,
        early_stopping_method="generate",
    )

    await test_agent_memory("ZERO_SHOT_REACT_DESCRIPTION", zero_shot_agent)
    await test_agent_memory("CONVERSATIONAL_REACT_DESCRIPTION", conversational_agent)


if __name__ == "__main__":
    asyncio.run(main())



from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


def elaborate_thought(last_tool_output: str):
    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.5)
    return llm.invoke(
        [
            SystemMessage(
                content=(
                    """Based on your personality, output an internal thought that led you to this decision based on the last tool output."""
                )
            ),
            HumanMessage(content="Your last tool output was: " + last_tool_output),
        ]
    )

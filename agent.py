import os
from typing import List, Tuple

from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_openai import ChatOpenAI
from tools import (
    execute_swap_tool,
    get_wallet_balance_tool,
    get_wallet_balance_in_sol_values_tool,
    navigate_url_tool,
    trending_coins_tool,
    get_token_info_tool,
)

os.getenv("LANGCHAIN_TRACING_V2")
os.getenv("LANGCHAIN_ENDPOINT")
os.getenv("LANGCHAIN_API_KEY")
os.getenv("LANGCHAIN_PROJECT")

with open("avatars/Misha/prompts/system.txt", "r") as file:
    assistant_system_message = file.read()

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", assistant_system_message),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
tools = [
    execute_swap_tool,
    get_wallet_balance_tool,
    get_wallet_balance_in_sol_values_tool,
    navigate_url_tool,
    trending_coins_tool,
    get_token_info_tool,
]
llm_with_tools = llm.bind(functions=[convert_to_openai_function(t) for t in tools])


def _format_chat_history(chat_history: List[Tuple[str, str]]):
    buffer = []
    for human, ai in chat_history:
        buffer.append(HumanMessage(content=human))
        buffer.append(AIMessage(content=ai))
    return buffer


agent = (
    {
        "input": lambda x: x["input"],
        "chat_history": lambda x: _format_chat_history(x["chat_history"]),
        "agent_scratchpad": lambda x: format_to_openai_function_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm_with_tools
    | OpenAIFunctionsAgentOutputParser()
)


class AgentInput(BaseModel):
    input: str
    chat_history: List[Tuple[str, str]] = Field(
        ..., extra={"widget": {"type": "chat", "input": "input", "output": "output"}}
    )


agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False).with_types(
    input_type=AgentInput
)

if __name__ == "__main__":
    chat_history = []
    user_input = """Start trading. Don't stop until you execute a swap. 
    Always remember to use as max amount the amount of the coin in your wallet you want to swap."""
    response = agent_executor.invoke(
        {"input": user_input, "chat_history": chat_history}
    )

    # loop 2 times
    for i in range(2):
        print("Misha:", response["output"])
        chat_history.append((user_input, response["output"]))
        user_input = """Keep trading"""
        response = agent_executor.invoke(
            {"input": user_input, "chat_history": chat_history}
        )

# for chunk in agent_executor.stream(
#     {"input": "Can you tell me what is your wallet balance?"}
# ):
#     # Agent Action
#     if "actions" in chunk:
#         for action in chunk["actions"]:
#             print(
#                 f"Calling Tool ```{action.tool}``` with input ```{action.tool_input}```"
#             )
#     # Observation
#     elif "steps" in chunk:
#         for step in chunk["steps"]:
#             print(f"Got result: ```{step.observation}```")

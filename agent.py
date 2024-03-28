import json
import asyncio
import random
import string

from datetime import date

from typing import Dict
from fastapi import WebSocket

from elevenlabs.client import ElevenLabs
from elevenlabs import play, save


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
    # navigate_url_tool,
    # trending_coins_tool,
    get_token_info_tool,
    tavily_search,
)


class AvatarAgent:
    def __init__(self):
        self.websocket = None
        self.prompt = None
        self.llm = None
        self.llm_with_tools = None
        self.agent = None
        self.agent_executor = None
        self.eleven_labs = ElevenLabs()

    def _generate_audio(self, text: str):
        audio = self.eleven_labs.generate(
            text=text, voice="Rachel", model="eleven_monolingual_v1"
        )
        random_string = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=8)
        )
        save(audio, "audio/" + random_string + ".mp3")
        return f"http://localhost:8000/audio/{random_string}.mp3"

    def _format_chat_history(self, chat_history: List[Tuple[str, str]]):
        buffer = []
        for human, ai in chat_history:
            buffer.append(HumanMessage(content=human))
            buffer.append(AIMessage(content=ai))
        return buffer

    def set_websocket(self, websocket: WebSocket):
        self.websocket = websocket

    async def process_message(
        self, user_message: str, chat_history: List[Tuple[str, str]]
    ):
        chat_history.append((user_message, ""))
        return chat_history

    async def invoke(self, input_text: str, chat_history: List[Tuple[str, str]]):
        return await self.agent_executor.ainvoke(
            {"input": input_text, "chat_history": chat_history}
        )

    async def stream(self, input_text: str, chat_history: List[Tuple[str, str]]):
        async for chunk in self.agent_executor.astream(
            {"input": input_text, "chat_history": chat_history}
        ):
            actions = chunk.get("actions", [])
            messages = chunk.get("messages", [])
            steps = chunk.get("steps", [])
            output = chunk.get("output", "")
            audio = ""

            print("actions", actions)
            print("messages", messages)
            print("steps", steps)
            print("output", output)

            # stringified actions and messages and steps to send to the frontend
            actions_str = json.dumps([action.json() for action in actions])
            messages_str = json.dumps([message.json() for message in messages])
            steps_str = json.dumps([step.json() for step in steps])

            # if output and len(output) > 0:
            #     audio = self._generate_audio(output)

            if self.websocket:
                await self.websocket.send_json(
                    {
                        "type": "internal_thought",
                        "action": actions_str,
                        "messages": messages_str,
                        "steps": steps_str,
                        "output": output,
                        "audio": audio,
                    }
                )

    async def start(self, name: str):
        with open(f"avatars/{name}/prompts/system.txt", "r") as file:
            assistant_system_message = file.read()

        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview", temperature=0, streaming=True
        )

        tools = [
            execute_swap_tool,
            get_wallet_balance_tool,
            get_wallet_balance_in_sol_values_tool,
            # navigate_url_tool,
            # trending_coins_tool,
            get_token_info_tool,
            tavily_search,
        ]
        self.llm_with_tools = self.llm.bind(
            functions=[convert_to_openai_function(t) for t in tools]
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", assistant_system_message),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # Define the agent
        self.agent = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: self._format_chat_history(x["chat_history"]),
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
            }
            | self.prompt
            | self.llm_with_tools
            | OpenAIFunctionsAgentOutputParser()
        )

        # Define the agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent, tools=tools, return_intermediate_steps=True
        ).with_types(input_type=AgentInput)

        today = date.today()
        user_input = """Be concise and start trading. 
		Remember that today is {today}.
		Always use the tools provided to help you make the best trades.
		Search online for info to help you make the best trades based on your personality. 
		When trading SOL always use at max 0.1 SOL."""
        # user_input = "Tell me a joke"
        return await self.stream(user_input, [])


class AgentInput(BaseModel):
    input: str
    chat_history: List[Tuple[str, str]] = Field(
        ..., extra={"widget": {"type": "chat", "input": "input", "output": "output"}}
    )


if __name__ == "__main__":
    agent = AvatarAgent()
    asyncio.run(agent.start("Misha"))
    chat_history = []
    user_input = "Start trading. Don't stop until you execute a swap."
    # user_input = "Tell me a joke and read it out for me."
    response = asyncio.run(agent.stream(user_input, chat_history))

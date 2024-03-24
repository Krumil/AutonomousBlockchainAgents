import os
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple
from agent import agent_executor

app = FastAPI()

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    input: str
    chat_history: List[Tuple[str, str]]


@app.post("/chat")
async def chat(message: ChatMessage):
    try:
        response = agent_executor.invoke(
            {"input": message.input, "chat_history": message.chat_history}
        )

        # Update chat history for continuity in conversation
        updated_chat_history = message.chat_history + [
            (message.input, response["output"])
        ]

        return {"output": response["output"], "chat_history": updated_chat_history}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# get endpoint to get the name of every folder inside the folders avatar
@app.get("/avatars")
async def get_avatar():
    try:
        avatars = os.listdir("avatars")
        formatted_avatars = []  # This correctly initializes an empty list
        for avatar in avatars:
            with open(f"avatars/{avatar}/prompts/system.txt") as f:
                system = f.read()
            # Append a new dictionary to the list for each avatar
            formatted_avatars.append(
                {
                    "system": system,
                    "portrait": f"avatars/{avatar}/images/portrait.jpg",
                    "name": avatar,
                }
            )

        return {"avatars": formatted_avatars}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Tuple
from agent import AvatarAgent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/avatars", StaticFiles(directory="avatars"), name="avatars")


class ChatMessage(BaseModel):
    input: str
    chat_history: List[Tuple[str, str]]


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    agent_instance = AvatarAgent()
    agent_instance.set_websocket(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "start":
                response = await agent_instance.start()
                await websocket.send_json(response)
            elif data.get("type") == "message":
                response = await agent_instance.process_message(data["message"])
                await websocket.send_json(response)
            elif data.get("type") == "avatar":
                response = get_avatar()
                await websocket.send_json({"type": "avatar", "data": response})

    except Exception as e:
        print(e)
    finally:
        await websocket.close()


def get_avatar():
    try:
        avatars = os.listdir("avatars")
        formatted_avatars = []
        root = os.getenv("ROOT_URL", "http://localhost:8000")
        for avatar in avatars:
            with open(f"avatars/{avatar}/prompts/system.txt") as f:
                system = f.read()
            formatted_avatars.append(
                {
                    "system": system,
                    "portrait": f"{root}/avatars/{avatar}/images/portrait.jpg",
                    "name": avatar,
                }
            )

        return {"avatars": formatted_avatars}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import json
import random
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
connections = {}
rooms = {}
origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return "I work!"

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    
    user = User(ws)
    try:
        while True:
            try:
                data = await ws.receive_text()  # on reçoit en texte
                content = json.loads(data)      # parse JSON
                
                if not user.logged_in and content["action"] != "login":
                    await ws.send_json({"error": "You are not logged in"})
                    continue
                
                action = content["action"]
                if action == "login": # {"action": "login", "username": "username"}
                    await user.login(content)
                elif action == "join": # {"action": "join", "room": "room_name"}
                    await user.join_room(content)
                elif action == "send": # {"action": "send", "room": "room_name", "message": "message"}
                    await user.send_message(content)
                # traitement ici
            except json.JSONDecodeError:
                # ignore ou log l’erreur
                print("Message reçu invalide :", data)
            
    except WebSocketDisconnect:
        await user.logout()

class User():
    def __init__(self, ws: WebSocket):
        self.username = ""
        self.logged_in = False
        self.my_rooms = []
        self.ws = ws
    
    async def login(self, content: dict):
        users = connections.keys()
        username = content["username"]
        if not username in users:
            connections[username] = self
            self.username = username
            self.logged_in = True
            await self.send_response("Logged in", "login")
        else:
            await self.send_error(f"User {username} already exists")
    
    async def logout(self):
        
        if self.username in connections:
            connections.pop(self.username)
        self.username = None
        self.logged_in = False
        
        for room in self.my_rooms:
            await self.leave_room({"room": room}, False)
        
    async def join_room(self, content: dict):
        room_name = content["room"]
        rooms.setdefault(room_name, set()).add(self)
        self.my_rooms.append(room_name)
        await self.send_response(f"Joined room {room_name}", "join")

    async def leave_room(self, content, verbose: bool = True):
        room_name = content["room"]
        if room_name in self.my_rooms:
            self.my_rooms.remove(room_name)
            rooms[room_name].remove(self)
        if verbose:
            await self.send_response(f"Left room {room_name}", "leave_room")
    async def send_message(self, content: dict):
        room_name = content["room"]
        message = content["message"]
        if room_name not in rooms:
            await self.send_error(f"Room {room_name} does not exist")
            return
        
        if room_name not in self.my_rooms or self not in rooms[room_name]:
            await self.send_error("You are not in this room")
            return
        await self.broadcast_room(room_name, message)
        
    async def broadcast_room(self, room_name: str, content: str):
        for user in rooms[room_name]:
            await user.relay_message(self.username, room_name, content)
            
    async def send_response(self, content:str, action: str):
        try:
            await self.ws.send_json({"action": action, "success": True, "error": "", "content": content})
        except WebSocketDisconnect:
            print("Disconnected")
            await self.logout()
            
    async def send_error(self, error: str):
        try:
            await self.ws.send_json({"action": "error", "success": False, "error": error})
        except WebSocketDisconnect:
            print("Disconnected")
            await self.logout()
    async def relay_message(self, from_user, from_room, content):
        try:
            await self.ws.send_json({"action": "receive_message", "from_user": from_user, "from_room": from_room, "content": content})
        except WebSocketDisconnect:
            print("Disconnected")
            await self.logout()
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
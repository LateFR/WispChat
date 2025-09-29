import asyncio
import json
import time
import jwt
import os
from datetime import datetime, timedelta, UTC
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Response
from fastapi.middleware.cors import CORSMiddleware
from matchmacker import MatchMaker
from threading import Thread
import uuid

SECRET_KEY = os.environ.get("SECRET_KEY", "secret123")
if SECRET_KEY == "secret123":
    print("WARNING: SECRET_KEY is set to the default value. Please change it in production.")
ALGORITHM = "HS256"
EXPIRE_MINUTES = int(os.environ.get("EXPIRE_MINUTES", 60))
connections = {} # {username: {"ws": WebSocket, "rooms": []}}
rooms = {} # {room_name: set(usernames)}
origins = ["http://localhost:5173", "http://192.168.1.49:5173"]

match_maker = MatchMaker()


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return None
        return username
    except jwt.ExpiredSignatureError as e:
        return None
    except jwt.InvalidTokenError:
        return None
    
async def lifespan(app: FastAPI):
    asyncio.create_task(matchmaking_loop())
    yield
    # shutdown code here

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def matchmaking_loop():
    global match_maker, connections
    while True:
        match = match_maker.find_match()
        if match:
            player1info, player2info = match
            player1,player2 = player1info["username"], player2info["username"]
            try: 
                user1 = connections[player1]
                user2 = connections[player2]
            except KeyError:
                if player1 in connections:
                    match_maker.add_player(player1, player1info)
                if player2 in connections:
                    match_maker.add_player(player2, player2info)
                continue
            if not user1.active or not user2.active:
                if user1.active:
                    match_maker.add_player(player1, player1info)
                if user2.active:
                    match_maker.add_player(player2, player2info)
                continue
            print(f"Match found: {player1} vs {player2}")
            room_id = str(uuid.uuid4())
            await user1.send_response({"room": room_id, "username": player2}, "matched")
            await user2.send_response({"room": room_id, "username": player1}, "matched")
        await asyncio.sleep(0.1)

@app.get("/")
async def read_root():
    return "I work!"

@app.get("/token")
async def get_token(username: str):
    users = connections.keys()
    if username in users:
        return Response(status_code=409, content=f"Username {username} already exists")
    expire = datetime.now(UTC) + timedelta(minutes=EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"token": token}

@app.get("/token/validate")
async def validate_token(token: str):
    username = verify_token(token)
    if username:
        return Response(status_code=200, content=username)
    else:
        return Response(status_code=401, content="Invalid token")

@app.get("/token/logout")
async def logout(token: str):
    username = verify_token(token)
    if username:
        if username in connections:
            await connections[username].logout()
        return Response(status_code=200, content="Logged out")
    else:
        return Response(status_code=400, content="Invalid token")
    
@app.post("/matchmaking/join")
async def join_matchmaking(request: Request):
    token = request.headers.get("Authorization", None)
    if not token:
        return Response(status_code=401, content="Invalid token")
    username = verify_token(token)
    if not username:
        return Response(status_code=401, content="Invalid token")
    
    if username in connections:
        match_maker.add_player(username, {"username": username})
        return Response(status_code=200, content="Joined matchmaking")
    else:
        return Response(status_code=403, content="Need login first")
    
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    token = ws.query_params["token"]
    username = verify_token(token)
    if username:
        await ws.accept()
    else:
        await ws.close(code=403, reason="Invalid token")
        return
    
    user = User(ws, username)
    try:
        while True:
            try:
                data = await ws.receive_text()  # on reçoit en texte
                content = json.loads(data)      # parse JSON
                
                
                action = content["action"]
                if action == "join": # {"action": "join", "room": "room_name"}
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
    def __init__(self, ws: WebSocket, username: str):
        self.username = username
        self.my_rooms = []
        self.ws = ws
        self.active = True
        
        connections[username] = self
    
    async def logout(self):
    # Supprimer l'utilisateur des connexions et des rooms d'abord
        self.active = False
        
        if self.username in connections:
            connections.pop(self.username)
        
        # Nettoyer les rooms sans envoyer de messages
        for room in list(self.my_rooms):  # list() pour éviter modification en boucle
            await self.leave_room({"room": room}, verbose=False)

        # Fermer la WS si elle est ouverte
        try:
            await self.ws.close()
        except RuntimeError:
            # La connexion est déjà fermée
            pass
        
    async def join_room(self, content: dict):
        room_name = content["room"]
        rooms.setdefault(room_name, set()).add(self.username)
        self.my_rooms.append(room_name)
        await self.send_response(f"Joined room {room_name}", "join")

    async def leave_room(self, content, verbose: bool = True):
        room_name = content["room"]
        if room_name in self.my_rooms:
            self.my_rooms.remove(room_name)
            rooms[room_name].remove(self.username)
        if verbose:
            await self.send_response(f"Left room {room_name}", "leave_room")
        
    async def send_message(self, content: dict):
        room_name = content["room"]
        message = content["message"]
        if room_name not in rooms:
            await self.send_error(f"Room {room_name} does not exist")
            return
        
        if room_name not in self.my_rooms or self.username not in rooms[room_name]:
            await self.send_error("You are not in this room")
            return
        await self.broadcast_room(room_name, message)
        
    async def broadcast_room(self, room_name: str, content: str):
        for username in rooms[room_name]:
            await connections[username].relay_message(self.username, room_name, content)
            
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
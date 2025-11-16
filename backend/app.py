# app.py
import asyncio
import json
import random
import re
from fastapi.websockets import WebSocketState
import httpx
import jwt
import os
from datetime import datetime, timedelta, UTC
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, Response
from fastapi.middleware.cors import CORSMiddleware
from matchmacker import MatchMaker
import redis.asyncio as aioredis
import uuid
import secrets
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "secret123")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(32)
    print("⚠️ WARNING: Using a temporary random SECRET_KEY — tokens won't persist across restarts.")
ALGORITHM = "HS256"
EXPIRE_MINUTES = int(os.environ.get("EXPIRE_MINUTES", 60))
USERNAME_ACCEPTED_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

connections = {} # {username: User}
connections_lock = asyncio.Lock()
rooms = {} # {room_name: set(usernames)}
origins = ["http://localhost:5173", "http://192.168.1.50:5173"]
temp_data_setup = {}
match_maker = MatchMaker()

with open('config.json') as f:
    config = json.load(f)

REDIS_HOST = config["redis"]["host"]
REDIS_PORT = config["redis"]["port"]
REDIS_DB = config["redis"]["db"]
REDIS_PASSWORD = config["redis"]["password"]
REDIS_MATCHMAKER_KEY = config["redis"]["redis_keys"]["matchmaking"]
redis_client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD, decode_responses=True)
BROKEN_CONNECTIONS_KEY = config["redis"]["redis_keys"]["broked_connections"]
REDIS_TTL = config["redis"]["ttl"]
ALL_MODES = config["match"]["modes"]

hcaptcha_enabled = config["hcaptcha"]["enabled"]
if hcaptcha_enabled:
    HSECRET = os.environ.get("HSECRET", None)
    if not HSECRET:
        raise ValueError("Missing HSECRET environment variable")

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

async def verify_hcaptcha(token: str, secret_key: str) -> bool:
    url = "https://hcaptcha.com/siteverify"
    params = {
        "secret": secret_key,
        "response": token
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, params=params)
        result = response.json()
        return result.get("success", False)

async def lifespan(app: FastAPI):
    task = asyncio.create_task(safe_matchmaking_loop())
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
    modes = ["chill", "date"]
    while True:
        for mode in modes:
            match = await match_maker.find_match(mode)
            if match:
                player1info, player2info = match
                player1, player2 = player1info["username"], player2info["username"]
                
                async with connections_lock:
                    try:
                        user1 = connections[player1]
                        user2 = connections[player2]
                    except KeyError:
                        player1_still_connected = player1 in connections
                        player2_still_connected = player2 in connections
                        if player1_still_connected and not player2_still_connected:
                            await match_maker.add_player(player1, player1info["gender"], player1info["age"], player1info["interests"], mode)
                        
                        if player2_still_connected and not player1_still_connected:
                            await match_maker.add_player(player2, player2info["gender"], player2info["age"], player2info["interests"], mode)
                        
                        await asyncio.sleep(0.1)
                        continue

                    if not user1.active or not user2.active:
                        if user1.active:
                            await match_maker.add_player(player1, player1info["gender"], player1info["age"], player1info["interests"], mode)
                        if user2.active:
                            await match_maker.add_player(player2, player2info["gender"], player2info["age"], player2info["interests"], mode)
                        await asyncio.sleep(0.1)
                        continue

                    print(f"Match found: {player1} vs {player2}")
                    room_id = str(uuid.uuid4())
                                    
                await user1.send_response({"room": room_id, "user": {"username": player2, "gender": player2info["gender"]}}, "matched")
                await user2.send_response({"room": room_id, "user": {"username": player1, "gender": player1info["gender"]}}, "matched")
                await asyncio.sleep(0.2)
        await asyncio.sleep(0.1) # Empêche la boucle de tourner à vide trop vite

async def safe_matchmaking_loop():
    while True:
        try:
            print("Starting matchmaking loop")
            await matchmaking_loop()
        except Exception as e:
            print(f"[ERROR] matchmaking loop crashed: {e}")
            await asyncio.sleep(1)

async def get_broken_users():
    cursor = 0
    broken_users = []
    while True:
        cursor, users = await redis_client.scan(cursor=cursor, match=f"{BROKEN_CONNECTIONS_KEY}:*", count=100)
        if users:
            broken_users.extend(users)
        if cursor == 0:
            break
    return [k.split(":", 1)[1] for k in broken_users]

@app.get("/")
async def read_root():
    return "I work!"

@app.get("/token")
async def get_token(username: str, request: Request):
    async with connections_lock:
        users = connections.keys()
    
    if not USERNAME_ACCEPTED_PATTERN.match(username):
        return Response(
            status_code=400,
            content="Invalid username format"
        )
    
    if username in users:
        return Response(status_code=409, content=f"Username {username} already taken")
    
    if hcaptcha_enabled:
        hcaptcha_token = request.headers.get("hcaptcha-token", None)
        if not hcaptcha_token:
            return Response(status_code=401, content="Invalid token")
        
        valid = await verify_hcaptcha(hcaptcha_token, HSECRET)
        if not valid:
            return Response(status_code=401, content="Invalid token")
            
    expire = datetime.now(UTC) + timedelta(minutes=EXPIRE_MINUTES)
    username = username[:20]
    payload = {"sub": username, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"token": token}

@app.get("/token/username-exist")
async def get_username_exist(username: str):
    if not USERNAME_ACCEPTED_PATTERN.match(username):
        raise HTTPException(status_code=400, detail="Invalid username format")
    
    async with connections_lock:
        exist = username in connections
            
    return {"exist": exist}

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
    
    if username not in connections:
        return Response(status_code=403, content="Need login first")
    
    user = connections[username]
    if not user.active or not user.GENDER or not user.AGE or not user.INTERESTS or not user.mode:
        return Response(status_code=403, content="User setup is not complete")
        
    for mode_to_remove in ALL_MODES:
        if mode_to_remove != user.mode:
            await match_maker.remove_player(username, mode_to_remove, ignore_error=True)
            
    await match_maker.add_player(username, user.GENDER, user.AGE, user.INTERESTS, user.mode)
    return Response(status_code=200, content="Joined matchmaking")

@app.post("/setup/info")
async def setup_info(request: Request):
    token = request.headers.get("Authorization", None)
    if not token:
        return Response(status_code=401, content="Invalid token")
    username = verify_token(token)
    if not username:
        return Response(status_code=401, content="Invalid token")
                
    data = await request.json()
    age = data.get("age", None)
    gender = data.get("gender", None)
    interests = data.get("interests", [])
    
    if not age or not gender or not isinstance(age, int) or age < 18 or gender not in ["male", "female"] or not interests:
        return Response(status_code=400, content="Missing or invalid fields")
        
    temp_data_setup[username] = {"age": age, "gender": gender, "interests": interests, "datetime": datetime.now()}
    return Response(status_code=200, content="Setup info received")

@app.post("/setup/mode")
async def setup_mode(request: Request):
    token = request.headers.get("Authorization", None)
    username = verify_token(token)
    if not username:
        return Response(status_code=401, content="Invalid token")
        
    data = await request.json()
    mode = data.get("mode", None)
    print(mode)
    if not mode or mode not in ["chill", "date", "interests"]:
        return Response(status_code=400, content="Missing or invalid mode")
        
    if username in connections:
        connections[username].mode = mode.lower()
        print(connections[username].mode)
        return Response(status_code=200, content="Mode updated")
    elif username in temp_data_setup:
        temp_data_setup[username]["mode"] = mode.lower()
        return Response(status_code=200, content="Mode updated")
    else:
        return Response(status_code=403, content="Need login first")

@app.get("/matchmaking/stats/people")
async def people_live(request: Request):
    token = request.headers.get("Authorization", None)
    username = verify_token(token)
    if not username:
        return Response(status_code=401, content="Invalid token")
        
    # Cette partie semble incomplète, je la laisse telle quelle
    for mode in match_maker.keys:
        len(await redis_client.hkeys(mode))

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=4401, reason="Token missing")
        return

    username = verify_token(token)
    if not username:
        await ws.close(code=4401, reason="Invalid token")
        return
        
    await ws.accept()
    
    user = None
    try:
        async with connections_lock:
            if username in connections:
                old_user = connections[username]
                # Fermer l'ancienne connexion si elle est toujours active
                if old_user.ws and old_user.ws.client_state != WebSocketState.DISCONNECTED:
                    try:
                        await old_user.ws.close(code=1000, reason="New connection established")
                    except Exception:
                        pass # Ignorer les erreurs si la socket est déjà fermée
                old_user.ws = ws
                old_user.active = True
                user = old_user
                print(f"✅ User {username} reconnected - WebSocket updated")
            else:
                broken_users = await get_broken_users()
                if username in temp_data_setup:
                    data = temp_data_setup[username]
                elif username in broken_users:
                    data = json.loads(await redis_client.get(f"{BROKEN_CONNECTIONS_KEY}:{username}"))
                    await redis_client.delete(f"{BROKEN_CONNECTIONS_KEY}:{username}")
                else:
                    await ws.close(code=1008, reason="Setup info missing")
                    return
                
                user = User(ws, username, data)
                connections[username] = user
                print(f"✅ User {username} connected for the first time.")

        # Boucle de réception des messages
        while True:
            data = await ws.receive_text()
            try:
                content = json.loads(data)
                action = content.get("action")
                
                if action == "join":
                    await user.join_room(content)
                elif action == "leave_room":
                    await user.leave_room(content)
                elif action == "send":
                    await user.send_message(content)
                            
            except json.JSONDecodeError:
                print("Message reçu invalide :", data)
    
    except WebSocketDisconnect:
        print(f"[{username}] WebSocket disconnected (state: {ws.client_state})")
    except Exception as e:
        print(f"[{username}] Error in websocket loop: {e}")
    finally:
        # ---- MODIFICATION IMPORTANTE ----
        # Ne déconnecter l'utilisateur que si sa connexion actuelle est bien
        # celle qui vient de se fermer. S'il s'est déjà reconnecté, user.ws
        # pointera vers la NOUVELLE websocket, et non plus vers 'ws'.
        if user and user.ws is ws:
            print(f"[{username}] Cleaning up connection as it's the last active one.")
            await user.logout()
        else:
            # Si 'user.ws' est différent de 'ws', cela signifie qu'une nouvelle
            # connexion a déjà pris le relais. L'ancienne instance se termine
            # sans rien faire pour ne pas déconnecter l'utilisateur actif.
            print(f"[{username}] Old connection instance for a reconnected user is closing. No cleanup needed.")


class User():
    def __init__(self, ws: WebSocket, username: str, setup_info: dict):
        self.username = username
        self.my_rooms = []
        self.ws = ws
        self.active = True
        self._logout_called = False
                
        self.GENDER = setup_info["gender"]
        self.AGE = setup_info["age"]
        self.INTERESTS = setup_info["interests"]
        self.mode = setup_info.get("mode", "date")
                
        if username in temp_data_setup:
            temp_data_setup.pop(username)
        
    async def logout(self):
        if self._logout_called:
            return
        self._logout_called = True
                
        print(f"[{self.username}] Logging out...")
        self.active = False
                
        async with connections_lock:
            if self.username in connections:
                # Sauvegarder l'état dans Redis pour une future reconnexion
                await redis_client.set(f"{BROKEN_CONNECTIONS_KEY}:{self.username}", json.dumps({
                    "gender": self.GENDER,
                    "age": self.AGE,
                    "interests": self.INTERESTS,
                    "mode": self.mode
                }), ex=REDIS_TTL * 60)
                
                # Retirer des connexions actives
                connections.pop(self.username)

        # Retirer du matchmaking
        for mode in ALL_MODES:
            await match_maker.remove_player(self.username, mode, ignore_error=True)
                
        # Nettoyer les rooms
        for room in list(self.my_rooms):
            await self.leave_room({"room": room}, verbose=False)
                
        # Fermer la WS si elle est encore ouverte
        try:
            if self.ws.client_state == WebSocketState.CONNECTED:
                await self.ws.close(code=1000, reason="User logged out")
        except Exception as e:
            print(f"[{self.username}] Error closing websocket during logout: {e}")

    async def join_room(self, content: dict):
        room_name = content["room"]
        rooms.setdefault(room_name, set()).add(self.username)
        if room_name not in self.my_rooms:
            self.my_rooms.append(room_name)
        await self.send_response(f"Joined room {room_name}", "join")

    async def leave_room(self, content, verbose: bool = True):
        room_name = content["room"]
        if room_name in self.my_rooms:
            self.my_rooms.remove(room_name)
            if room_name in rooms:
                rooms[room_name].discard(self.username)
                if verbose:
                    print(f"[{self.username}] Left room", room_name)
                    await self.send_response(f"Left room {room_name}", "leave_room")
                
                remaining_users = rooms.get(room_name)
                if remaining_users and len(remaining_users) == 0:
                    rooms.pop(room_name)
                    return
                
                if remaining_users:
                    for username in list(remaining_users):
                        if username in connections:
                            await connections[username].send_response(self.username, "user_left")

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
        if room_name not in rooms:
            return
        for username in list(rooms[room_name]):
            if username in connections:
                await connections[username].relay_message(self.username, room_name, content)

    async def send_response(self, content, action: str):
        if not self.active:
            return
        try:
            if self.ws.client_state == WebSocketState.CONNECTED:
                await self.ws.send_json({"action": action, "success": True, "error": "", "content": content})
        except Exception as e:
            print(f"[{self.username}] Error sending response: {e}")

    async def send_error(self, error: str):
        if not self.active:
            return
        try:
            if self.ws.client_state == WebSocketState.CONNECTED:
                await self.ws.send_json({"action": "error", "success": False, "error": error})
        except Exception as e:
            print(f"[{self.username}] Error sending error: {e}")

    async def relay_message(self, from_user, from_room, content):
        if not self.active:
            return
        try:
            if self.ws.client_state == WebSocketState.CONNECTED:
                await self.ws.send_json({"action": "receive_message", "content": {"message": content, "from_user": from_user, "from_room": from_room}})
        except Exception as e:
            print(f"[{self.username}] Error relaying message: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=True)
import asyncio
import json
import random
from fastapi.websockets import WebSocketState
import httpx
import jwt
import os
from datetime import datetime, timedelta, UTC
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Response
from fastapi.middleware.cors import CORSMiddleware
from matchmacker import MatchMaker
import redis
import uuid
import secrets

SECRET_KEY = os.environ.get("SECRET_KEY", "secret123")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(32)
    print("⚠️ WARNING: Using a temporary random SECRET_KEY — tokens won't persist across restarts.")

ALGORITHM = "HS256"
EXPIRE_MINUTES = int(os.environ.get("EXPIRE_MINUTES", 60))
connections = {} # {username: {"ws": WebSocket, "rooms": []}}

rooms = {} # {room_name: set(usernames)}
origins = ["http://localhost:5173", "http://192.168.1.49:5173"]
temp_data_setup = {}

match_maker = MatchMaker()

with open('config.json') as f:
    config = json.load(f)

REDIS_HOST = config["redis"]["host"]
REDIS_PORT = config["redis"]["port"]
REDIS_DB = config["redis"]["db"]
REDIS_PASSWORD = config["redis"]["password"]
REDIS_MATCHMAKER_KEY = config["redis"]["redis_keys"]["matchmaking"]
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD, decode_responses=True)

BROKEN_CONNECTIONS_KEY = config["redis"]["redis_keys"]["broked_connections"]
REDIS_TTL = config["redis"]["ttl"]

hcaptcha_enabled = config["hcaptcha"]["enabled"]

if hcaptcha_enabled:
    HSECRET = os.environ.get("HSECRET", None)
    if not HSECRET:
        raise ValueError("Missing HSECRET environment variable")
    
    
ALL_MODES = config["match"]["modes"]
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

async def verify_hcaptcha(token: str, secret_key: str = HSECRET) -> bool:
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
            match = match_maker.find_match(mode)
            if match:
                player1info, player2info = match
                player1, player2 = player1info["username"], player2info["username"]

                try: 
                    user1 = connections[player1]
                    user2 = connections[player2]
                except KeyError:
                    # Un ou deux joueurs se sont déconnectés entre le match et la vérification.
                    # On remet en file uniquement ceux qui sont ENCORE connectés.
                    # Le joueur déconnecté est simplement ignoré (il a déjà été retiré de Redis par find_match).
                    
                    player1_still_connected = player1 in connections
                    player2_still_connected = player2 in connections

                    if player1_still_connected and not player2_still_connected:
                        # player2 est parti, on remet player1 dans la file
                        match_maker.add_player(player1, player1info["gender"], player1info["age"], player1info["interests"], mode)
                    
                    if player2_still_connected and not player1_still_connected:
                        # player1 est parti, on remet player2 dans la file
                        match_maker.add_player(player2, player2info["gender"], player2info["age"], player2info["interests"], mode)
                    
                    # Si les deux sont déconnectés, on ne fait rien.
                    await asyncio.sleep(0.1)
                    continue

                # vérifier si les joueurs sont actifs
                if not user1.active or not user2.active:
                    if user1.active:
                        match_maker.add_player(player1, player1info["gender"], player1info["age"], player1info["interests"], mode)
                    if user2.active:
                        match_maker.add_player(player2, player2info["gender"], player2info["age"], player2info["interests"], mode)
                    await asyncio.sleep(0.1)
                    continue

                # match trouvé
                print(f"Match found: {player1} vs {player2}")
                room_id = str(uuid.uuid4())
                await user1.send_response({"room": room_id, "user": {"username": player2, "gender": player2info["gender"]}}, "matched")
                await user2.send_response({"room": room_id, "user": {"username": player1, "gender": player1info["gender"]}}, "matched")

        await asyncio.sleep(0.2)

async def safe_matchmaking_loop():
    while True:
        try:
            print("Starting matchmaking loop")
            await matchmaking_loop()
        except Exception as e:
            print(f"[ERROR] matchmaking loop crashed: {e}")
            await asyncio.sleep(1)  # éviter crash en boucle infinie rapide

def get_brocken_users():
    cursor = 0
    broken_users = []
    
    while True:
        cursor, users = redis_client.scan(cursor=cursor, match=f"{BROKEN_CONNECTIONS_KEY}:*", count=100)
        if cursor == 0:
            break
        for user in users:
            broken_users.append(user)
    return [k.split(":")[1] for k in broken_users]

@app.get("/")
async def read_root():
    return "I work!"

@app.get("/token")
async def get_token(username: str, request: Request):
    users = connections.keys()
    if username in users:
        return Response(status_code=409, content=f"Username {username} already exists")
    
    if hcaptcha_enabled:
        hcaptcha_token = request.headers.get("hcaptcha-token", None)
        if not hcaptcha_token:
            return Response(status_code=401, content="Invalid token")
        
        valid = await verify_hcaptcha(hcaptcha_token, HSECRET)
        if not valid:
            return Response(status_code=401, content="Invalid token")
        
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
    
    if username not in connections:
        return Response(status_code=403, content="Need login first")
    
    user = connections[username]
    if not user.active or not user.GENDER or not user.AGE or not user.INTERESTS or not user.mode:
        return Response(status_code=403, content="Need login first")
    
    for mode_to_remove in ALL_MODES:
        if mode_to_remove != user.mode: # On ne se retire pas de la file qu'on veut rejoindre
            match_maker.remove_player(username, mode_to_remove, ignore_error=True)
            
    if username in connections:
        match_maker.add_player(username, user.GENDER, user.AGE, user.INTERESTS, user.mode)
        return Response(status_code=200, content="Joined matchmaking")
    else:
        return Response(status_code=403, content="Need login first")

@app.post("/setup/info")
async def setup_info(request: Request):
    token = request.headers.get("Authorization", None)
    if not token:
        return Response(status_code=401, content="Invalid token")
    username = verify_token(token)
    if not username:
        return Response(status_code=401, content="Invalid token")
    
    
    
    data = await request.json()
    age = int(data.get("age", None))
    gender = data.get("gender", None)
    interests = data.get("interests", [])
    
    if not age or not gender or age < 18 or gender not in ["male", "female"] or not interests:
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
    
    for mode in match_maker.keys:
        len(redis_client.hkeys(mode))
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    token = ws.query_params["token"]
    username = verify_token(token)
    if not username:
        await ws.close(code=403, reason="Invalid token")
        return
    
    broken_users = get_brocken_users()
    if username and username in temp_data_setup or username in broken_users:
        await ws.accept()
    elif username in list(connections.keys()):
        await ws.close(code=403, reason="Unauthorized")
        return
    elif not username in temp_data_setup and not username in broken_users:
        await ws.close(code=403, reason="Setup info missing")
        return
    else:
        await ws.close(code=403, reason="Invalid token")
        return
    
    
    if username in broken_users:
        data = json.loads(redis_client.get(f"{BROKEN_CONNECTIONS_KEY}:{username}"))
        redis_client.delete(f"{BROKEN_CONNECTIONS_KEY}:{username}")
        connections[username] = user
    else:
        data = temp_data_setup[username]
    user = User(ws, username, data)
    try:
        while True:
            try:
                data = await ws.receive_text()  # on reçoit en texte
                content = json.loads(data)      # parse JSON
                
                
                action = content["action"]
                if action == "join": # {"action": "join", "room": "room_name"}
                    await user.join_room(content)
                elif action == "leave_room": # {"action": "leave_room", "room": "room_name"}
                    await user.leave_room(content)
                elif action == "send": # {"action": "send", "room": "room_name", "message": "message"}
                    await user.send_message(content)
                # traitement ici
            except json.JSONDecodeError:
                # ignore ou log l’erreur
                print("Message reçu invalide :", data)
            
    except WebSocketDisconnect:
        await user.logout()

class User():
    def __init__(self, ws: WebSocket, username: str, setup_info: dict):
        self.username = username
        self.my_rooms = []
        self.ws = ws
        self.active = True
        
        connections[username] = self
        
        self.GENDER = setup_info["gender"]
        self.AGE = setup_info["age"]
        self.INTERESTS = setup_info["interests"]
        self.mode = setup_info.get("mode", "date")  # "chill", "date" or "interests"

        if username in temp_data_setup:
            temp_data_setup.pop(username)
            
    async def logout(self):
    # Supprimer l'utilisateur des connexions et des rooms d'abord
        self.active = False
        
        if self.username in connections:
            connections.pop(self.username)
            redis_client.set(f"{BROKEN_CONNECTIONS_KEY}:{self.username}", json.dumps({
                "gender": self.GENDER,
                "age": self.AGE,
                "interests": self.INTERESTS,
                "mode": self.mode
            }), ex=REDIS_TTL * 60) 
        
        for mode in ALL_MODES:
            match_maker.remove_player(self.username, mode, ignore_error=True)
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
            print("Left room", room_name)
            await self.send_response(f"Left room {room_name}", "leave_room")
        
        if len(list(rooms[room_name].copy())) == 0:
            rooms.pop(room_name)
            return
        
        for username in list(rooms[room_name].copy()):
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
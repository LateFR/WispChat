from typing import Literal
import redis
import json

with open('config.json') as f:
    config = json.load(f)

REDIS_HOST = config["redis"]["host"]
REDIS_PORT = config["redis"]["port"]
REDIS_DB = config["redis"]["db"]
REDIS_PASSWORD = config["redis"]["password"]
REDIS_MATCHMAKER_KEY = config["redis"]["redis_keys"]["matchmaking"]

class MatchMaker():
    def __init__(self):
        self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD, decode_responses=True)
        
        self.keys = {"chill": REDIS_MATCHMAKER_KEY + ":waiting_players:chill", "date": REDIS_MATCHMAKER_KEY + ":waiting_players:date"}
        
    def add_player(self, player:str, gender:str, age:int, interests:list, mode:Literal["chill", "date"]):
        self.redis.hset(self.keys[mode], player, json.dumps({"username":player, "gender": gender, "age": age, "interests": interests}))

    def remove_player(self, player, mode:Literal["chill", "date"], ignore_error = False):
        if ignore_error:
            try:
                self.redis.hdel(self.keys[mode], player)
            except:
                pass
        else:
            self.redis.hdel(self.keys[mode], player)

    def get_player(self, player:str, mode:Literal["chill", "date"], remove:bool=False):
        player_data = self.redis.hget(self.keys[mode], player)
        if player_data:
            try:
                data = json.loads(player_data)
            except json.JSONDecodeError:
                raise ValueError("Invalid player data")
            if remove:
                self.remove_player(player, mode)
            return data
        else:
            raise KeyError(f"Player {player} does not exist")
        
    def find_match(self, mode:Literal["chill", "date"]):
        waiting_players = self.redis.hkeys(self.keys[mode])
        if len(waiting_players) >= 2:
            player1 = self.get_player(waiting_players[0], remove=True, mode=mode)
            player2 = self.get_player(waiting_players[1], remove=True, mode=mode)
            return (player1, player2)
        return None
    
    
import asyncio
from typing import Literal
import redis.asyncio as aioredis
import json
import time

with open('config.json') as f:
    config = json.load(f)

REDIS_HOST = config["redis"]["host"]
REDIS_PORT = config["redis"]["port"]
REDIS_DB = config["redis"]["db"]
REDIS_PASSWORD = config["redis"]["password"]
REDIS_MATCHMAKER_KEY = config["redis"]["redis_keys"]["matchmaking"]

class MatchMaker():
    MAX_AGE_DIFFERENCE = 100

    def __init__(self):
        self.redis = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD, decode_responses=True)
        self.keys = {"chill": REDIS_MATCHMAKER_KEY + ":waiting_players:chill", "date": REDIS_MATCHMAKER_KEY + ":waiting_players:date"}

    async def add_player(self, player:str, gender:str, age:int, interests:list, mode:Literal["chill", "date"]):
        player_data = {
            "username": player,
            "gender": gender,
            "age": age,
            "interests": interests,
            "join_time": time.time()
        }
        await self.redis.hset(self.keys[mode], player, json.dumps(player_data))

    async def remove_player(self, player, mode:Literal["chill", "date"], ignore_error=False):
        try:
            await self.redis.hdel(self.keys[mode], player)
        except Exception as e:
            if not ignore_error:
                raise e

    async def get_player(self, player:str, mode:Literal["chill", "date"], remove:bool=False):
        # Cette fonction est moins utilisée maintenant mais on la garde pour le mode chill
        player_data = await self.redis.hget(self.keys[mode], player)
        if player_data:
            try:
                data = json.loads(player_data)
            except json.JSONDecodeError:
                raise ValueError("Invalid player data")
            if remove:
                await self.remove_player(player, mode)
            return data
        else:
            raise KeyError(f"Player {player} does not exist")

    
    async def find_match(self, mode:Literal["chill", "date"]):
        if mode == "chill":
            waiting_players = await self.redis.hkeys(self.keys[mode])
            if len(waiting_players) >= 2:
                player1 = await self.get_player(waiting_players[0], remove=True, mode=mode)
                player2 = await self.get_player(waiting_players[1], remove=True, mode=mode)
                return (player1, player2)
            return None

        if mode == "date":
            all_players_data = await self.redis.hgetall(self.keys[mode])
            if len(all_players_data) < 2:
                return None

            # 1. Séparer les joueurs par genre
            men = []
            women = []
            for username, data_str in all_players_data.items():
                try:
                    player = json.loads(data_str)
                    if player.get("gender") == "male":
                        men.append(player)
                    elif player.get("gender") == "female":
                        women.append(player)
                except (json.JSONDecodeError, TypeError):
                    continue
            
            # S'il n'y a pas au moins un homme et une femme, impossible de matcher
            if not men or not women:
                return None

            # 2. Trier le groupe prioritaire (femmes) par temps d'attente
            women.sort(key=lambda p: p.get("join_time", float('inf')))

            i = 0
            # 3. Itérer sur chaque femme (chercheuse) pour lui trouver le meilleur partenaire
            for woman in women:
                best_partner_for_her = None
                min_age_diff = float('inf')

                # On cherche le meilleur partenaire pour cette femme spécifique
                for man in men:
                    age_diff = abs(woman.get("age", 99) - man.get("age", 99))
                    if i % 10 == 0:
                        await asyncio.sleep(0) #let the loop keep the control
                    i+=1
                    if age_diff < min_age_diff:
                        min_age_diff = age_diff
                        best_partner_for_her = man
                
                # 4. Si un partenaire a été trouvé ET qu'il respecte le seuil
                if best_partner_for_her and min_age_diff <= self.MAX_AGE_DIFFERENCE:
                    # Match trouvé !
                    await self.remove_player(woman["username"], mode)
                    await self.remove_player(best_partner_for_her["username"], mode)
                    
                    # On retourne le match et on arrête la recherche pour ce cycle
                    return (woman, best_partner_for_her)

            # Si on a parcouru toutes les femmes sans trouver de match valide
            return None
        
        return None
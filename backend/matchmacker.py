class MatchMaker():
    def __init__(self):
        self.waiting_players = {}

    def add_player(self, player:str, gender:str, age:int, interests:list):
        self.waiting_players[player] = {"username":player, "gender": gender, "age": age, "interests": interests}

    def remove_player(self, player):
        if player in self.waiting_players:
            self.waiting_players.pop(player)

    def find_match(self):
        players = list(self.waiting_players.keys()) 
        if len(self.waiting_players) >= 2:
            player1 = self.waiting_players.pop(players[0])
            player2 = self.waiting_players.pop(players[1])
            return (player1, player2)
        return None
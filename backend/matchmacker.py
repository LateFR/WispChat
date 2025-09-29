class MatchMaker():
    def __init__(self):
        self.waiting_players = {}

    def add_player(self, player, info):
        self.waiting_players[player] = info

    def remove_player(self, player):
        if player in self.waiting_players:
            self.waiting_players.pop(player)

    def find_match(self):
        players = list(self.waiting_players.keys()) 
        if len(self.waiting_players) >= 2:
            player1 = self.waiting_players.pop(0)
            player2 = self.waiting_players.pop(0)
            return (player1, player2)
        return None
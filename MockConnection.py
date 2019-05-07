class MockConnection:
    def search_public(self):
        games = [
            { 
            "id":"aabbccdd",
            "name":"TestGame1",
            "level":"2",
            "difficulty":"Medium",
            "mode":"Classic",
            "num_players":1,
            "max_players":3
            },
                        { 
            "id":"aabbccd1",
            "name":"TestGame2",
            "level":"2",
            "difficulty":"Hard",
            "mode":"Classic",
            "num_players":1,
            "max_players":3
            },
            { 
            "id":"aabbccd2",
            "name":"TestGame3",
            "level":"2",
            "difficulty":"Easy",
            "mode":"Unlimited",
            "num_players":1,
            "max_players":3
            },
            { 
            "id":"aabbccd3",
            "name":"TestGame4",
            "level":"2",
            "difficulty":"Easy",
            "mode":"Unlimited",
            "num_players":1,
            "max_players":3
            }
        ]
        return games
    def search(self, password):
        return self.search_public()
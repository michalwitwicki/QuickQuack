import random
import json

class QuickQuackDatabase:
    NUM_MAPS = 3
    NUM_PLAYERS = 5

    def __init__(self, auto_populate=True):
        self.maps = {}
        self.players = {}
        self.records = {}
        if auto_populate:
            self.populate_database()

    def add_map(self, map_id):
        if map_id not in self.maps:
            self.maps[map_id] = {}

    def add_player(self, player_id):
        if player_id not in self.players:
            self.players[player_id] = {'average_rank': 0}

    def add_record(self, map_id, player_id, time):
        if map_id in self.maps and player_id in self.players:
            if map_id not in self.records:
                self.records[map_id] = {}

            if player_id not in self.records[map_id] or time < self.records[map_id][player_id]['time']:
                self.records[map_id][player_id] = {'time': time, 'rank': None}

                # Update ranks based on sorted times
                sorted_records = sorted(self.records[map_id].items(), key=lambda x: x[1]['time'])
                for idx, (pid, data) in enumerate(sorted_records):
                    self.records[map_id][pid]['rank'] = idx + 1

                # Update player's average rank
                total_rank = sum(data['rank'] for pid, data in sorted_records)
                self.players[player_id]['average_rank'] = total_rank / len(sorted_records)

    def get_player_average_rank(self, player_id):
        return self.players[player_id]['average_rank'] if player_id in self.players else 0

    def print_map_records(self, map_id):
        if map_id in self.records:
            print(f"Records for Map '{map_id}':")
            sorted_records = sorted(self.records[map_id].items(), key=lambda x: x[1]['time'])
            for player_id, data in sorted_records:
                print(f"Player: {player_id}, Time: {data['time']}, Rank: {data['rank']}")
        else:
            print(f"No records found for Map '{map_id}'")

    def print_player_records(self, player_id):
        print(f"Records for Player '{player_id}':")
        player_records = [(map_id, self.records[map_id][player_id]['time'], self.records[map_id][player_id]['rank']) for map_id in self.records.keys() if player_id in self.records[map_id]]
        if player_records:
            sorted_player_records = sorted(player_records, key=lambda x: x[1])
            for map_id, time, rank in sorted_player_records:
                print(f"Map: {map_id}, Time: {time}, Rank: {rank}")
        else:
            print(f"No records found for Player '{player_id}'")

    def dump_to_json(self, filename):
        data_to_dump = {
            'maps': self.maps,
            'players': self.players,
            'records': self.records
        }

        with open(filename, 'w') as json_file:
            json.dump(data_to_dump, json_file, indent=2)

    def load_from_json(self, filename):
        with open(filename, 'r') as json_file:
            loaded_data = json.load(json_file)

        self.maps = loaded_data.get('maps', {})
        self.players = loaded_data.get('players', {})
        self.records = loaded_data.get('records', {})

    def populate_database(self):
        # Add maps
        for i in range(1, self.NUM_MAPS + 1):
            map_id = f"Map{i}"
            self.add_map(map_id)

        # Add players
        for i in range(1, self.NUM_PLAYERS + 1):
            player_id = f"Player{i}"
            self.add_player(player_id)

        # Add random records
        for map_id in self.maps.keys():
            for player_id in self.players.keys():
                if random.choice([True, False]):  # Randomly decide if the player has a record on the map
                    time = random.uniform(1, 100)
                    self.add_record(map_id, player_id, time)

if __name__ == "__main__":
    game_db = QuickQuackDatabase(auto_populate=False)
    game_db.add_player("P1")
    game_db.add_player("P2")
    game_db.add_map("M1")
    game_db.add_map("M2")

    game_db.add_record("M1", "P1", 100)
    game_db.add_record("M1", "P2", 11)
    game_db.add_record("M2", "P1", 100)
    game_db.add_record("M2", "P2", 101)
    game_db.add_record("M3", "P2", 101)

    game_db.print_map_records("M1")
    game_db.print_map_records("M2")


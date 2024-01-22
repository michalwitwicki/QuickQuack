import random
import json

# Keys names as variables to make life easier
K_RECORDS_COUNT = 'records_count'
K_BEST_TIME = 'best_time'
K_WORST_TIME = 'worst_time'
K_AVERAGE_RANK = 'average_rank'
K_MAP_PARTICIPATION_COUNT = 'map_participation_count'
K_TIME = 'time'
K_RANK = 'rank'
K_NORM_RANK = 'time_normalized_rank'
K_NORM_CONFIDENCE = 'normalized_confidence'
K_TOTAL_PARTICIPATING_PLAYERS_COUNT = 'total_participating_players_count'
K_BASE_SCORE = 'base_score'

class QuickQuackDatabase:
    NUM_MAPS = 1
    NUM_PLAYERS = 17 
    NORM_RANK_RANGE = (10, 1)
    NORM_OPPONETS_BEHIND_FACTOR_RANGE = (1, 2)

    def __init__(self, auto_populate=True):
        # assumption:
        # "maps" is the map pool for a season
        self.maps = {}
        self.players = {}
        self.records = {}
        self.metadata = {K_TOTAL_PARTICIPATING_PLAYERS_COUNT: 0}
        if auto_populate:
            self.populate_database()

    def add_map(self, map_id):
        if map_id not in self.maps:
            self.maps[map_id] = {
                K_RECORDS_COUNT: 0,
                K_BEST_TIME: None,
                K_WORST_TIME: None
            }

    def add_player(self, player_id):
        if player_id not in self.players:
            self.players[player_id] = {
                K_AVERAGE_RANK: None,
                K_MAP_PARTICIPATION_COUNT: 0,
            }
            # self.players[player_id] = {K_MAP_PARTICIPATION_COUNT: 0}

    def add_record(self, map_id, player_id, time):
        if map_id in self.maps and player_id in self.players:
            if map_id not in self.records:
                self.records[map_id] = {}
            
            # Increase counters
            tmp = True
            for m_id, records in self.records.items():
                if player_id in self.records[m_id]:
                    tmp = False
                    break

            if tmp == True:
                self.metadata[K_TOTAL_PARTICIPATING_PLAYERS_COUNT] += 1

            if player_id not in self.records[map_id]:
                self.players[player_id][K_MAP_PARTICIPATION_COUNT] += 1
                self.maps[map_id][K_RECORDS_COUNT] += 1

            if player_id not in self.records[map_id] or time < self.records[map_id][player_id][K_TIME]:
                self.records[map_id][player_id] = {
                    K_TIME: time,
                    K_RANK: None,
                    K_NORM_RANK: None,
                    K_NORM_CONFIDENCE: None,
                    K_BASE_SCORE: None
                }

                self.__update_map_ranks(map_id)
                self.__update_map_norm_ranks(map_id)
                self.__update_map_confidence(map_id)
                self.__update_map_base_score(map_id)
                self.__update_players_avg_ranks(map_id)

        else:
            print(f"Map '{map_id}' or player '{player_id}' not found")

    def get_player_average_rank(self, player_id):
        return self.players[player_id][K_AVERAGE_RANK] if player_id in self.players else 0

    def __update_map_ranks(self, map_id):
        # Update ranks based on sorted times
        sorted_records = sorted(self.records[map_id].items(), key=lambda x: x[1][K_TIME])

        self.maps[map_id][K_BEST_TIME] = sorted_records[0][1][K_TIME]
        self.maps[map_id][K_WORST_TIME] = sorted_records[-1][1][K_TIME]

        for idx, (pid, data) in enumerate(sorted_records):
            self.records[map_id][pid][K_RANK] = idx + 1

    def __update_map_norm_ranks(self, map_id):
        for pid, data in self.records[map_id].items():
            norm_rank = remap_to_range(
                self.records[map_id][pid][K_TIME],
                self.maps[map_id][K_BEST_TIME], self.maps[map_id][K_WORST_TIME],
                self.NORM_RANK_RANGE[0], self.NORM_RANK_RANGE[1]
            )

            self.records[map_id][pid][K_NORM_RANK] = round(norm_rank, 3)

    def __update_map_confidence(self, map_id):
        map_player_count = self.maps[map_id][K_RECORDS_COUNT]
        for pid, data in self.records[map_id].items():
            opponets_behind_count = map_player_count - self.records[map_id][pid][K_RANK];
            norm_confidence = remap_to_range(
                opponets_behind_count,
                0, self.metadata[K_TOTAL_PARTICIPATING_PLAYERS_COUNT] - 1,
                self.NORM_OPPONETS_BEHIND_FACTOR_RANGE[0], self.NORM_OPPONETS_BEHIND_FACTOR_RANGE[1]
            )

            self.records[map_id][pid][K_NORM_CONFIDENCE] = norm_confidence

    def __update_map_base_score(self, map_id):
        for pid, data in self.records[map_id].items():
            confidence = self.records[map_id][pid][K_NORM_CONFIDENCE]
            normalized_rank = self.records[map_id][pid][K_NORM_RANK]
            self.records[map_id][pid][K_BASE_SCORE] = normalized_rank * confidence

    def __update_players_avg_ranks(self, map_id):
        # Update players average rank

        for player_id in self.records[map_id]:
            total_rank = 0
            total_maps = 0

            for map_id, records in self.records.items():
                if player_id in records:
                    total_rank += records[player_id][K_RANK]
                    total_maps += 1

            if total_maps == 0:
                avg_rank = 0
                print("this should never happend!!!!")
            else:
                avg_rank = round(total_rank / total_maps, 3)

            self.players[player_id][K_AVERAGE_RANK] = avg_rank


    # -------------------------------------------------------------------------
    # --- Utilities ---
    # -------------------------------------------------------------------------

    def print_map_records(self, map_id):
        if map_id in self.records:
            print(f"Records for Map '{map_id}':")
            sorted_records = sorted(self.records[map_id].items(), key=lambda x: x[1][K_TIME])
            for player_id, data in sorted_records:
                print(f"Player: {player_id}, Time: {data[K_TIME]}, Rank: {data[K_RANK]}")
        else:
            print(f"No records found for Map '{map_id}'")

    def print_time_table(self, map_id):
        if map_id in self.records:
            sorted_records = sorted(self.records[map_id].items(), key=lambda x: x[1][K_TIME])

            # Print header
            print(f"{'Player ID': <15}{K_TIME: <10}{K_RANK: <10}{K_NORM_RANK: <25}{K_NORM_CONFIDENCE: <25}{K_BASE_SCORE: <15}")

            # Print data rows
            for player_id, data in sorted_records:
                print(f"{player_id: <15}{data[K_TIME]: <10}{data[K_RANK]: <10}{data.get(K_NORM_RANK, ''): <25}{data.get(K_NORM_CONFIDENCE, ''): <25}{data.get(K_BASE_SCORE, ''): <15}")
                # print(f"{player_id: <15}{data[K_TIME]: <10}{data[K_RANK]: <10}{data[K_NORM_RANK]: <25}{data[K_NORM_CONFIDENCE]: <25}{data[K_BASE_SCORE]: <15}")
        else:
            print(f"No records found for Map '{map_id}'")

    def print_player_records(self, player_id):
        print(f"Records for Player '{player_id}':")
        player_records = [(map_id, self.records[map_id][player_id][K_TIME], self.records[map_id][player_id][K_RANK]) for map_id in self.records.keys() if player_id in self.records[map_id]]
        if player_records:
            sorted_player_records = sorted(player_records, key=lambda x: x[1])
            for map_id, time, rank in sorted_player_records:
                print(f"Map: {map_id}, Time: {time}, Rank: {rank}")
        else:
            print(f"No records found for Player '{player_id}'")

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
                if random.random() < 0.75: # Randomly decide if the player has a record on the map
                    time = round(random.uniform(1, 100), 3)
                    self.add_record(map_id, player_id, time)

    def dump_to_json(self, filename):
        data_to_dump = {
            'maps': self.maps,
            'players': self.players,
            'records': self.records,
            'metadata': self.metadata
        }

        with open(filename, 'w') as json_file:
            json.dump(data_to_dump, json_file, indent=2)

    def load_from_json(self, filename):
        with open(filename, 'r') as json_file:
            loaded_data = json.load(json_file)

        self.maps = loaded_data.get('maps', {})
        self.players = loaded_data.get('players', {})
        self.records = loaded_data.get('records', {})
        self.metadata = loaded_data.get('metadata', {})

# Remap value 'x' from range 'ab' to range 'cd'
def  remap_to_range(value, from_low, from_high, to_low, to_high):
    if from_high == from_low:
        return max(to_low, to_high)

    scaled_value = (value - from_low) / (from_high - from_low)
    remapped_value = to_low + scaled_value * (to_high - to_low)

    return remapped_value

if __name__ == "__main__":
    game_db = QuickQuackDatabase()
    game_db.print_time_table("Map1")

    # game_db = QuickQuackDatabase(auto_populate=False)
    # game_db.add_player("P1")
    # game_db.add_player("P2")
    # game_db.add_player("P3")
    # # game_db.add_map("M1")
    # game_db.add_map("M2")
    # game_db.add_map("M3") 
    # game_db.add_record("M1", "P1", 10)
    # game_db.add_record("M1", "P2", 20)
    # game_db.add_record("M1", "P3", 30)
    # game_db.add_record("M1", "P2", 9)
    # game_db.add_record("M1", "P3", 123)
    # game_db.add_record("M1", "P2", 91)
    # game_db.add_record("M1", "P3", 8)

    # game_db.add_record("M2", "P1", 12)
    # game_db.add_record("M2", "P2", 91)
    # game_db.add_record("M2", "P3", 100)

    # game_db.add_record("M3", "P1", 12)
    # game_db.add_record("M3", "P2", 10)

    game_db.dump_to_json("db.json")

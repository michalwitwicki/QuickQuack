import random
import json

# Keys names as variables to make life easier
K_RECORDS_COUNT = 'records_count'
K_BEST_TIME = 'best_time'
K_WORST_TIME = 'worst_time'
K_AVG_RANK = 'avg_rank'
K_AVG_NORM_RANK = 'avg_norm_rank'
K_MAP_PARTICIPATION_COUNT = 'map_participation_count'
K_TIME = 'time'
K_RANK = 'rank'
K_NORM_RANK = 'normalized_rank'
K_CONFIDENCE_FACTOR = 'confidence_factor'
K_TOTAL_PARTICIPATING_PLAYERS_COUNT = 'total_participating_players_count'
K_BASE_SCORE = 'base_score'
K_MAP_ATTENDANCE_FACTOR = 'attendance_factor'
K_ATTENDANCE_SCORE = 'attendance_score'
K_AVG_CONFIDENCE_FACTOR = 'avg_confidence_factor'
K_AVG_BASE_SCORE = 'avg_base_score'
K_AVG_ATTENDANCE_SCORE = 'avg_attendance_score'
K_FINAL_SCORE = 'final_score'

class QuickQuackDatabase:
    NORM_RANK_RANGE = (10, 1)
    CONFIDENCE_FACTOR_RANGE = (0, 1)
    MAP_ATTENDANCE_FACTOR_RANGE = (1, 0)
    MAX_ATTENDANCE_BONUS = 10

    def __init__(self, auto_populate=True, num_maps=3, num_players=5):

        self.metadata = {K_TOTAL_PARTICIPATING_PLAYERS_COUNT: 0}
        self.maps = {} # "maps" dictionary is THE map pool for a season
        self.players = {}
        self.records = {}
        if auto_populate:
            self.populate_database(num_maps, num_players)

    def add_map(self, map_id):
        if map_id not in self.maps:
            self.maps[map_id] = {
                K_RECORDS_COUNT: 0,
                K_BEST_TIME: None,
                K_WORST_TIME: None,
                K_MAP_ATTENDANCE_FACTOR: None
            }

    def add_player(self, player_id):
        if player_id not in self.players:
            self.players[player_id] = {
                K_MAP_PARTICIPATION_COUNT: 0,
                K_AVG_RANK: None,
                K_AVG_NORM_RANK: None,
                K_AVG_CONFIDENCE_FACTOR: None,
                K_AVG_BASE_SCORE: None,
                K_AVG_ATTENDANCE_SCORE: None,
                K_FINAL_SCORE: None
            }

    def add_record(self, map_id, player_id, time):
        if map_id in self.maps and player_id in self.players:
            if map_id not in self.records:
                self.records[map_id] = {}
            
            attendance_factor_changed = False
            update_players_stats = False

            # Increase counters and calculate attendance factor and bonus
            if self.__update_counters(map_id, player_id):
                self.__update_attendance_factors(map_id, player_id)
                attendance_factor_changed = True
                update_players_stats = True

            # Add or update record
            if player_id not in self.records[map_id] or time < self.records[map_id][player_id][K_TIME]:
                self.records[map_id][player_id] = {
                    K_TIME: time,
                    K_RANK: None,
                    K_NORM_RANK: None,
                    K_CONFIDENCE_FACTOR: None,
                    K_BASE_SCORE: None,
                    K_ATTENDANCE_SCORE: None
                }

                self.__update_ranks(map_id)
                self.__update_norm_ranks(map_id)
                self.__update_players_avg_ranks(map_id)

                update_players_stats = True

            # Update stats depending on attendancy factor
            if attendance_factor_changed:
                # TODO: all of those methods shoube be merged into one for optimalization reasons
                self.__update_attendance_bonuses()
                self.__update_confidences()
                self.__update_base_scores()

            # Update players stats if something important changed
            if update_players_stats:
                self.__update_players_stats()

        else:
            print(f"Map '{map_id}' or player '{player_id}' not found")

    def __update_counters(self, map_id, player_id):
        # This method returns True if TOTAL_PARTICIPATING_PLAYERS_COUNT or RECORDS_COUNT changed 

        # Update total participating players count
        tmp = True
        for m_id, records in self.records.items():
            if player_id in self.records[m_id]:
                tmp = False
                break

        if tmp == True:
            self.metadata[K_TOTAL_PARTICIPATING_PLAYERS_COUNT] += 1

        # Update another counters
        if player_id not in self.records[map_id]:
            self.players[player_id][K_MAP_PARTICIPATION_COUNT] += 1
            self.maps[map_id][K_RECORDS_COUNT] += 1
            return True

        if tmp == True:
            return True

        return False

    def __update_attendance_factors(self, map_id, player_id):
        # Update attendance only if player is not yet recorded on on the map
        if player_id in self.records[map_id]:
            return

        total_participating_players_count = self.metadata[K_TOTAL_PARTICIPATING_PLAYERS_COUNT]

        for m_id in self.maps:
            map_records_count = self.maps[m_id][K_RECORDS_COUNT]
            if map_records_count == 0:
                continue

            attendance_factor = remap_to_range(map_records_count,
                                                1, total_participating_players_count,
                                                self.MAP_ATTENDANCE_FACTOR_RANGE[0], 
                                                self.MAP_ATTENDANCE_FACTOR_RANGE[1])

            self.maps[m_id][K_MAP_ATTENDANCE_FACTOR] = round(attendance_factor, 3)

    def __update_attendance_bonuses(self):
        # Update attendance bonus everywhere!
        for m_id, records in self.records.items():
            attendance_factor = self.maps[m_id][K_MAP_ATTENDANCE_FACTOR]
            for p_id, data in records.items():
                self.records[m_id][p_id][K_ATTENDANCE_SCORE] = round(attendance_factor * self.MAX_ATTENDANCE_BONUS, 3)

    def __update_ranks(self, map_id):
        # Update ranks based on sorted times
        sorted_records = sorted(self.records[map_id].items(), key=lambda x: x[1][K_TIME])

        self.maps[map_id][K_BEST_TIME] = sorted_records[0][1][K_TIME]
        self.maps[map_id][K_WORST_TIME] = sorted_records[-1][1][K_TIME]

        for idx, (p_id, data) in enumerate(sorted_records):
            self.records[map_id][p_id][K_RANK] = idx + 1

    def __update_norm_ranks(self, map_id):
        for p_id, data in self.records[map_id].items():
            norm_rank = remap_to_range(
                self.records[map_id][p_id][K_TIME],
                self.maps[map_id][K_BEST_TIME], self.maps[map_id][K_WORST_TIME],
                self.NORM_RANK_RANGE[0], self.NORM_RANK_RANGE[1]
            )

            self.records[map_id][p_id][K_NORM_RANK] = round(norm_rank, 3)

    def __update_confidences(self):
        for m_id, records in self.records.items():
            map_player_count = self.maps[m_id][K_RECORDS_COUNT]
            for p_id, data in records.items():
                opponets_behind_count = map_player_count - self.records[m_id][p_id][K_RANK];

                if opponets_behind_count == 0:
                    norm_confidence = self.CONFIDENCE_FACTOR_RANGE[0]
                else:
                    norm_confidence = remap_to_range(
                        opponets_behind_count,
                        0, self.metadata[K_TOTAL_PARTICIPATING_PLAYERS_COUNT] - 1,
                        self.CONFIDENCE_FACTOR_RANGE[0], self.CONFIDENCE_FACTOR_RANGE[1]
                    )

                self.records[m_id][p_id][K_CONFIDENCE_FACTOR] = round(norm_confidence, 3)

    def __update_base_scores(self):
        for m_id, records in self.records.items():
            for p_id, data in records.items():
                confidence = self.records[m_id][p_id][K_CONFIDENCE_FACTOR]
                normalized_rank = self.records[m_id][p_id][K_NORM_RANK]
                self.records[m_id][p_id][K_BASE_SCORE] = round(normalized_rank * confidence, 3)

    def __update_players_avg_ranks(self, map_id):
        # Update players average rank
        for player_id in self.records[map_id]:
            total_rank = 0
            total_norm_rank = 0
            total_maps = 0

            for map_id, records in self.records.items():
                if player_id in records:
                    total_rank += records[player_id][K_RANK]
                    total_norm_rank += records[player_id][K_NORM_RANK]
                    total_maps += 1

            if total_maps == 0:
                continue
            else:
                avg_rank = round(total_rank / total_maps, 3)
                avg_norm_rank = round(total_norm_rank / total_maps, 3)

            self.players[player_id][K_AVG_RANK] = avg_rank
            self.players[player_id][K_AVG_NORM_RANK] = avg_norm_rank

    def __update_players_stats(self):

        for p_id, data in self.players.items():
            total_maps = 0
            total_confidence_factor = 0
            total_base_score = 0
            total_attendance_score = 0
            final_score = 0

            for m_id, records in self.records.items():
                if p_id in records:
                    total_maps += 1
                    total_confidence_factor += records[p_id][K_CONFIDENCE_FACTOR]
                    total_base_score += records[p_id][K_BASE_SCORE]
                    total_attendance_score += records[p_id][K_ATTENDANCE_SCORE]

            if total_maps == 0:
                continue
            else:
                avg_confidence_factor = round(total_confidence_factor / total_maps, 3)
                avg_base_score = round(total_base_score / total_maps, 3)
                avg_attendance_score = round(total_attendance_score / total_maps, 3)
                final_score = round(avg_base_score + avg_attendance_score, 3)

            self.players[p_id][K_AVG_CONFIDENCE_FACTOR] = avg_confidence_factor
            self.players[p_id][K_AVG_BASE_SCORE] = avg_base_score
            self.players[p_id][K_AVG_ATTENDANCE_SCORE] = avg_attendance_score
            self.players[p_id][K_FINAL_SCORE] = final_score



    # -------------------------------------------------------------------------
    # --- Utilities ---
    # -------------------------------------------------------------------------

    def print_map_time_table(self, map_id):
        if map_id not in self.records:
            print(f"No records found for Map '{map_id}'")
            return

        print(f"Records for map '{map_id}':")

        sorted_records = sorted(self.records[map_id].items(), key=lambda x: x[1][K_TIME])

        # Print header
        print(f"{'Player ID': <15}{K_TIME: <10}{K_RANK: <10}{K_NORM_RANK: <25}{K_CONFIDENCE_FACTOR: <25}{K_BASE_SCORE: <15}{K_ATTENDANCE_SCORE: <15}")

        # Print data rows
        for player_id, data in sorted_records:
            print(f"{player_id: <15}{data[K_TIME]: <10}{data[K_RANK]: <10}{data[K_NORM_RANK]: <25}{data[K_CONFIDENCE_FACTOR]: <25}{data[K_BASE_SCORE]: <15}{data[K_ATTENDANCE_SCORE]: <15}")

        print(f"\nStats for map '{map_id}':")
        for data in self.maps[map_id].items():
            print(f"{data[0]}: {data[1]}")

    def print_player_time_table(self, player_id):
        print(f"Records for player '{player_id}':")
        player_records = [(map_id,
                           self.records[map_id][player_id][K_TIME],
                           self.records[map_id][player_id][K_RANK],
                           self.records[map_id][player_id][K_NORM_RANK],
                           self.records[map_id][player_id][K_CONFIDENCE_FACTOR],
                           self.records[map_id][player_id][K_BASE_SCORE],
                           self.records[map_id][player_id][K_ATTENDANCE_SCORE],
                           )
                           for map_id in self.records.keys() if player_id in self.records[map_id]]

        if not player_records:
            print(f"No records found for Player '{player_id}'")
            return

        sorted_player_records = sorted(player_records, key=lambda x: x[2])

        # Print header
        print(f"{'Map ID': <15}{K_TIME: <10}{K_RANK: <10}{K_NORM_RANK: <25}"
              f"{K_CONFIDENCE_FACTOR: <25}{K_BASE_SCORE: <15}{K_ATTENDANCE_SCORE: <15}")

        # Print data rows
        for data in sorted_player_records:
            print(f"{data[0]: <15}{data[1]: <10}{data[2]: <10}{data[3]: <25}{data[4]: <25}{data[5]: <15}{data[6]: <15}")

        print(f"\nStats for player '{player_id}':")
        for data in self.players[player_id].items():
            print(f"{data[0]}: {data[1]}")

    def print_leader_board(self):

        sorted_players = sorted(self.players.items(), key=lambda x: x[1][K_FINAL_SCORE], reverse=True)

        # Print header
        print(f"{'Player ID': <11}{K_MAP_PARTICIPATION_COUNT: <25}{K_AVG_RANK: <10}{K_AVG_NORM_RANK: <15}"
              f"{K_AVG_CONFIDENCE_FACTOR: <23}{K_AVG_BASE_SCORE: <16}{K_AVG_ATTENDANCE_SCORE: <22}{K_FINAL_SCORE: <15}")

        # Print data rows
        for player_id, data in sorted_players:
            print(f"{player_id: <11}{data[K_MAP_PARTICIPATION_COUNT]: <25}{data[K_AVG_RANK]: <10}"
                  f"{data[K_AVG_NORM_RANK]: <15}{data[K_AVG_CONFIDENCE_FACTOR]: <23}"
                  f"{data[K_AVG_BASE_SCORE]: <16}{data[K_AVG_ATTENDANCE_SCORE]: <22}{data[K_FINAL_SCORE]: <15}")

    def populate_database(self, num_maps, num_players):
        # Add maps
        for i in range(1, num_maps + 1):
            map_id = f"Map{i}"
            self.add_map(map_id)

        # Add players
        for i in range(1, num_players + 1):
            player_id = f"Player{i}"
            self.add_player(player_id)

        # Add simulation data for maps
        SIM_MAP_POPULARITY = 'popularity'
        SIM_MAP_BEST_TIME = 'best_time'
        SIM_MAP_WORST_TIME = 'worst_time'
        maps_simulation_data = {}
        for m_id in self.maps:
            time1 = random.uniform(3, 100)
            time2 = random.uniform(3, 100)
            maps_simulation_data[m_id] = {
                SIM_MAP_POPULARITY: round(random.random(), 3),
                SIM_MAP_BEST_TIME: round(min(time1, time2), 3),
                SIM_MAP_WORST_TIME: round(max(time1, time2), 3)
            }

        pretty = json.dumps(maps_simulation_data, indent=4)
        print(pretty)

        # Add simulation data for players
        SIM_PLAYER_SKILL = 'player_skill' # expressed as the percentile of opponents that a given player will defeat
        SIM_NUM_TRIES = 'num_tries'
        SIM_NUM_TRIES_MAX = 5
        players_simulation_data = {}
        for p_id in self.players:
            player_skill = round(random.random(), 3)
            num_tries = int(player_skill * SIM_NUM_TRIES_MAX) + 1
            players_simulation_data[p_id] = {
                SIM_PLAYER_SKILL: player_skill,
                SIM_NUM_TRIES: num_tries
            }

        pretty = json.dumps(players_simulation_data, indent=4)
        print(pretty)

        # Add records
        for m_id in self.maps.keys():
            for p_id in self.players.keys():
                for i in range(players_simulation_data[p_id][SIM_NUM_TRIES]):
                    if maps_simulation_data[m_id][SIM_MAP_POPULARITY] >= random.random():
                        time = remap_to_range(
                                players_simulation_data[p_id][SIM_PLAYER_SKILL],
                                0, 1,
                                maps_simulation_data[m_id][SIM_MAP_WORST_TIME],
                                maps_simulation_data[m_id][SIM_MAP_BEST_TIME]
                                )
                        print(f"time: {time}")
                        self.add_record(m_id, p_id, round(time, 3))
                        break

    def dump_to_json(self, filename):
        data_to_dump = {
            'metadata': self.metadata,
            'maps': self.maps,
            'players': self.players,
            'records': self.records
        }

        with open(filename, 'w') as json_file:
            json.dump(data_to_dump, json_file, indent=2)

    def load_from_json(self, filename):
        with open(filename, 'r') as json_file:
            loaded_data = json.load(json_file)

        self.metadata = loaded_data.get('metadata', {})
        self.maps = loaded_data.get('maps', {})
        self.players = loaded_data.get('players', {})
        self.records = loaded_data.get('records', {})

# Remap value 'x' from range 'ab' to range 'cd'
def  remap_to_range(value, from_low, from_high, to_low, to_high):
    if from_high == from_low:
        return max(to_low, to_high)

    scaled_value = (value - from_low) / (from_high - from_low)
    remapped_value = to_low + scaled_value * (to_high - to_low)

    return remapped_value

if __name__ == "__main__":
    game_db = QuickQuackDatabase(num_maps=1, num_players=1)
    # game_db = QuickQuackDatabase(num_maps=3, num_players=2)
    # game_db.print_map_time_table("Map1")
    # game_db.print_player_time_table("Player1")
    # game_db.print_leader_board()

    # game_db = QuickQuackDatabase(auto_populate=False)
    # game_db.add_map("M1")
    # game_db.add_map("M2")
    # game_db.add_player("P1")
    # game_db.add_player("P2")
    # game_db.add_player("P3")
    # game_db.add_player("P4")
    # game_db.add_player("P5")
    # game_db.add_player("P6")
    # game_db.add_player("P7")
    # game_db.add_player("P8")
    # game_db.add_player("P9")
    # game_db.add_player("P10")

    # game_db.add_record("M1", "P1", 10)
    # game_db.add_record("M1", "P2", 20)
    # game_db.add_record("M1", "P3", 9)
    # game_db.add_record("M1", "P4", 30)
    # game_db.add_record("M1", "P5", 1)
    # game_db.add_record("M1", "P6", 10)
    # game_db.add_record("M1", "P7", 20)
    # game_db.add_record("M1", "P8", 30)
    # # game_db.add_record("M1", "P9", 9)
    # # game_db.add_record("M1", "P10", 123)

    # game_db.add_record("M2", "P9", 20)
    # game_db.add_record("M2", "P10", 10)



    game_db.dump_to_json("db.json")

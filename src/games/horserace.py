# coding: utf-8

import time
import array
import random
from games.game_base import CommonGameBase, CommonPlayer


class HorseRacePlayer(CommonPlayer):
    def __init__(self):
        super(HorseRacePlayer, self).__init__()
        self.move_log = array.array('B')
        self.total_distance = 0

    def serialize(self):
        return self.move_log.tostring()

    def move(self, distance):
        self.move_log.append(distance)
        self.total_distance += distance

    def punish(self, distance):
        self.move_log[-1] -= distance
        self.total_distance -= distance

    def reward(self, distance):
        self.move_log[-1] += distance
        self.total_distance += distance

    def upgrade(self):
        self.move_log[-1] += 1
        self.total_distance += 1

    def __gt__(self, other):
        return self.total_distance > other.total_distance

    def __lt__(self, other):
        return self.total_distance < other.total_distance

    def __eq__(self, other):
        return self.total_distance == other.total_distance


class HorseRace(CommonGameBase):
    def __init__(self):
        super(HorseRace, self).__init__()
        self.slot_count = 3
        self.race_time = 10
        self.min_speed = 4  # make sure min speed bigger than 2
        self.max_speed = 12

    def get_slot_count(self):
        return self.slot_count

    def generate_players(self):
        players = [HorseRacePlayer() for _ in range(self.slot_count)]
        seed = int(time.time() * 1000) % self.slot_count
        for i in range(self.race_time):
            for j, player in enumerate(players):
                move_distance = random.randint(self.min_speed, self.max_speed)
                move_distance += (0 if j != seed else 1)
                player.move(move_distance)
        return players

    def get_winner_index(self, results):
        max_index = 0
        for i in range(1, len(results)):
            cur = results[i]
            if results[max_index] < cur:
                max_index = i
            elif results[max_index] == cur:
                # 出现相等情况时，升级当前最快的马，使之的确最快
                results[max_index].upgrade()
        return max_index

    @staticmethod
    def convert_result(players):
        return [player.move_log.tolist() for player in players]

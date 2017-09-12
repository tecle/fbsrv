# coding: utf-8

import random
from games.game_base import CommonGameBase, CommonGameResult
from collections import namedtuple

CarInfo = namedtuple('CarInfo', ['name', 'odds'])


class CarLoops(CommonGameBase):
    def __init__(self):
        super(CarLoops, self).__init__()
        self.car_repeat_times = 4

    def get_slot_count(self):
        return 6

    def play_game(self, winner_slot=None):
        which_car = random.randint(0, self.car_repeat_times - 1)
        if winner_slot is None:
            winner_slot = random.randint(0, self.get_slot_count() - 1)
        return CommonGameResult(
            result_list=which_car, winner_index=winner_slot, detail=self.convert_result(which_car))

    def serialize_game_result(self, result):
        return 'idx:{}|win:{}'.format(result.result_list, result.winner_index)

    @staticmethod
    def convert_result(which_car):
        return {'car': which_car}

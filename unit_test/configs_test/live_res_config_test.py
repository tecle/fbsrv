# coding: utf-8

import unittest
import os
from configs.live_res_config import GameConfig
from games.zhajinhua import ZhaJinHua


class LiveResConfigTest(unittest.TestCase):
    def get_game_config(self):
        CUR_PATH = os.path.split(os.path.realpath(__file__))[0]
        return GameConfig(os.path.join(CUR_PATH, 'game_list.json'))

    def test_parse_json_file(self):
        gc = self.get_game_config()
        self.assertEqual(1, len(gc.games_list))
        self.assertEqual(1, len(gc.games_map))
        self.assertEqual(4, len(gc.games_list[0].status))

    def test_get_game_impl(self):
        gc = self.get_game_config()
        inst = gc.get_game_impl(2)
        self.assertTrue(isinstance(inst, ZhaJinHua))

    def test_get_type_from_tag(self):
        gc = self.get_game_config()
        self.assertEqual(2, gc.get_type_from_tag('ZhaJinHua')[0])

    def test_get_multiple(self):
        gc = self.get_game_config()
        self.assertEqual(4, gc.get_multiple_by_game(2, 1))

    def test_get_earned(self):
        gc = self.get_game_config()
        res = gc.get_earned(2, 0, {1: 10, 2: 50})
        self.assertEqual([(1, 20), (2, 100)], res)

    def test_robot(self):
        gc = self.get_game_config()
        rbt = gc.get_robot()
        rbt.reset(100, 3)
        print rbt.bet()
        print rbt.bet()
        print rbt.bet()

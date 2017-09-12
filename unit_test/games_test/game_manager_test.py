# coding: utf-8

import json
import unittest

import games.game_manager as GM
import mock

from configs.live_res_config import GameConfig, Robot
from configs.live_res_config import GameStatus
from games.niuniu import NiuNiuFor3Player
from model.cache import CacheWrapper
from model.cache import UserResCache
from thirdsupport.yunxin import YunXinAPI

MockGameConfig = mock.create_autospec(GameConfig)
MockCacheWrapper = mock.create_autospec(CacheWrapper)
MockUserResCache = mock.create_autospec(UserResCache)
MockBroadCaster = mock.create_autospec(YunXinAPI)
MockRobot = mock.create_autospec(Robot)


class GameManagerTest(unittest.TestCase):
    def start_gm_with_game(self, uid, room_id):
        gm = self.make_game_manager()
        gm.game_config.get_game_status_list.return_value = [
            GameStatus(1, GM.GameStatusCode.ST_Waiting),
            GameStatus(2, GM.GameStatusCode.ST_Betting),
            GameStatus(3, GM.GameStatusCode.ST_ShowResult)
        ]

        resp = gm.start_game(uid, room_id, 1, 100, 'A')
        obj = json.loads(resp)
        self.assertEqual('OK', obj['status'])
        self.assertEqual(0, obj['code'])
        self.assertEqual(200, obj['body']['Data']['code'])
        self.assertEqual(1, len(gm.game_adapters))
        self.assertEqual(0, len(gm.stopping_adapters))
        return gm

    @staticmethod
    def make_game_manager():
        mock_game_cfg = MockGameConfig('123')
        robot = MockRobot('bet_config')
        mock_game_cfg.get_robot = lambda: robot
        reset_args = None

        def fake_reset(*args):
            reset_args = args

        robot.reset = fake_reset
        robot.bet.return_value = (1, 10)
        cw = MockCacheWrapper('redis')
        mock_user_res_cache = MockUserResCache('')
        mock_user_res_cache.consume_gold.return_value = (True, '')
        cw.get_cache.return_value = mock_user_res_cache

        gm = GM.GameManager(
            mock_game_cfg, MockCacheWrapper('redis'), MockBroadCaster(1, 2, 3, 4))
        gm.game_config.get_game_impl.return_value = NiuNiuFor3Player()
        return gm

    def test_start_game(self):
        gm = self.make_game_manager()
        resp = gm.start_game(1, 2, 1, 100, 'A')
        obj = json.loads(resp)
        self.assertEqual(200, obj['body']['Data']['code'])
        self.assertEqual(100, obj['body']['ReqId'])

    def test_time_event(self):
        gm = self.start_gm_with_game(1, 2)
        ga = gm.game_adapters.get(1)
        self.assertEqual(0, ga.game_status_index)
        self.assertEqual(1, ga.adapter_status)
        self.assertEqual(2, ga.room_id)

        # ga.cache.is_user_living.return_value = True
        gm.time_event()
        # ga.cache.is_user_living.assert_called_with(1)
        self.assertEqual(0, ga.progress)
        self.assertEqual(3, len(ga.game_status_list))
        self.assertTrue(ga is not None)
        self.assertEqual(2, ga.room_id)
        self.assertEqual(1, ga.game_type)
        self.assertEqual(1, ga.game_status_index)
        call_args = gm.game_broadcaster.send_msg_to_chatroom.call_args
        self.assertEqual(2, call_args[0][0])

        gm.time_event()
        self.assertEqual(1, ga.progress)
        self.assertEqual(1, ga.game_status_index)

        # 进行游戏
        ga.game_config.decide_winner.return_value = 1
        gm.time_event()
        self.assertEqual(0, ga.progress)
        self.assertEqual(2, ga.game_status_index)
        # call_args = gm.game_broadcaster.send_msg_to_chatroom.call_args
        # print call_args[0][1]

        gm.time_event()
        self.assertEqual(1, ga.progress)
        self.assertEqual(2, ga.game_status_index)
        gm.time_event()
        gm.time_event()
        self.assertEqual(0, ga.progress)
        self.assertEqual(0, ga.game_status_index)

    def test_stop_game(self):
        gm = self.start_gm_with_game(1, 2)
        gm._stop_game(1)
        self.assertEqual(0, len(gm.game_adapters))
        self.assertEqual(1, len(gm.stopping_adapters))

    def test_get_game_snapshot(self):
        gm = self.start_gm_with_game(1, 2)
        resp = gm.get_game_snapshot(1, 2, 101, 'A')
        obj = json.loads(resp)
        self.assertEqual(101, obj['body']['ReqId'])
        self.assertEqual(200, obj['body']['Data']['code'])
        self.assertEqual(0, obj['body']['Data']['sec'])
        self.assertEqual(1, obj['body']['Data']['st'])
        self.assertEqual([0, 0, 0], obj['body']['Data']['uBet'])
        self.assertEqual([0, 0, 0], obj['body']['Data']['sBet'])

        gm.time_event()
        resp = gm.get_game_snapshot(1, 2, 102, 'A')
        obj = json.loads(resp)
        self.assertEqual(0, obj['body']['Data']['sec'])
        self.assertEqual(2, obj['body']['Data']['st'])

        gm.time_event()
        resp = gm.get_game_snapshot(1, 2, 102, 'A')
        obj = json.loads(resp)
        self.assertEqual(1, obj['body']['Data']['sec'])
        self.assertEqual(2, obj['body']['Data']['st'])

        resp = gm.add_bet(1, 10086, 1, 50, 103, 'A')
        obj = json.loads(resp)
        self.assertEqual(200, obj['body']['Data']['code'])

        resp = gm.add_bet(1, 10000, 1, 30, 103, 'A')
        obj = json.loads(resp)
        self.assertEqual(200, obj['body']['Data']['code'])

        resp = gm.add_bet(1, 10000, 0, 30, 103, 'A')
        obj = json.loads(resp)
        self.assertEqual(200, obj['body']['Data']['code'])

        resp = gm.get_game_snapshot(1, 10086, 101, 'A')
        obj = json.loads(resp)
        self.assertEqual(200, obj['body']['Data']['code'])
        self.assertEqual([0, 50, 0], obj['body']['Data']['uBet'])
        self.assertEqual([30, 80, 0], obj['body']['Data']['sBet'])

    def test_start_multi_games(self):
        gm = self.start_gm_with_game(1, 10086)
        resp = gm.start_game(2, 10000, 1, 999, 'A')
        obj = json.loads(resp)
        self.assertEqual(200, obj['body']['Data']['code'])
        self.assertEqual(2, len(gm.game_adapters))
        self.assertEqual(0, len(gm.stopping_adapters))
        gm.time_event()
        self.assertEqual(0, gm.game_adapters[1].progress)
        self.assertEqual(0, gm.game_adapters[2].progress)
        gm.time_event()
        self.assertEqual(1, gm.game_adapters[1].game_status_index)
        self.assertEqual(1, gm.game_adapters[2].game_status_index)

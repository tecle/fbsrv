# coding: utf-8
import logging
from games.cards import CardInfo
import games.game_base as GameBase


class FakeTaxasResult(object):
    def __init__(self, game_cls, player_cls):
        self.lwin_result_list = []
        self.equal_result_list = []
        self.rwin_result_list = []
        self.equal_idx = 0
        self.lwin_idx = 0
        self.game_cls = game_cls
        self.process_fake_data(player_cls)

    def process_fake_data(self, player_cls):
        for cards in self.get_fake_lwin_data():
            player1 = player_cls(cards[:7])
            player2 = player_cls(cards[-7:])
            self.lwin_result_list.append(
                GameBase.CommonGameResult(
                    result_list=(player1, player2, cards), winner_index=0,
                    detail=self.game_cls.convert_result((player1, player2, cards))))
            self.rwin_result_list.append(
                GameBase.CommonGameResult(
                    result_list=(player2, player1, cards[-2:] + cards[2:6] + cards[:2]), winner_index=2,
                    detail=self.game_cls.convert_result((player2, player1, cards))))

        for cards in self.get_fake_equal_data():
            player1 = player_cls(cards[:7])
            player2 = player_cls(cards[-7:])
            self.equal_result_list.append(
                GameBase.CommonGameResult(
                    result_list=(player1, player2, cards), winner_index=1,
                    detail=self.game_cls.convert_result((player1, player2, cards))))

    def get_result(self, winner_slot):
        logging.info('[taxas] fake result for winner slot:{}'.format(winner_slot))
        if winner_slot == 1:
            self.equal_idx += 1
            if self.equal_idx >= len(self.equal_result_list):
                self.equal_idx = 0
            return self.equal_result_list[self.equal_idx]
        else:
            self.lwin_idx += 1
            if self.lwin_idx >= len(self.lwin_result_list):
                self.lwin_idx = 0
            return self.lwin_result_list[self.lwin_idx] if winner_slot < 1 else self.rwin_result_list[self.lwin_idx]

    def get_fake_lwin_data(self):
        return (
            [CardInfo(type=1, value=11), CardInfo(type=3, value=13), CardInfo(type=4, value=4),
             CardInfo(type=3, value=3),
             CardInfo(type=2, value=2), CardInfo(type=4, value=11), CardInfo(type=4, value=3),
             CardInfo(type=3, value=7),
             CardInfo(type=4, value=9)],
            [CardInfo(type=1, value=10), CardInfo(type=4, value=10), CardInfo(type=3, value=4),
             CardInfo(type=2, value=11),
             CardInfo(type=4, value=6), CardInfo(type=1, value=9), CardInfo(type=1, value=12),
             CardInfo(type=4, value=2),
             CardInfo(type=3, value=9)],
            [CardInfo(type=2, value=2), CardInfo(type=1, value=13), CardInfo(type=3, value=5),
             CardInfo(type=2, value=5),
             CardInfo(type=1, value=2), CardInfo(type=4, value=2), CardInfo(type=3, value=11),
             CardInfo(type=4, value=9),
             CardInfo(type=2, value=10)],
            [CardInfo(type=4, value=10), CardInfo(type=4, value=7), CardInfo(type=4, value=9),
             CardInfo(type=2, value=4),
             CardInfo(type=4, value=1), CardInfo(type=4, value=11), CardInfo(type=2, value=6),
             CardInfo(type=4, value=8),
             CardInfo(type=1, value=1)],
            [CardInfo(type=3, value=8), CardInfo(type=4, value=3), CardInfo(type=4, value=13),
             CardInfo(type=3, value=11),
             CardInfo(type=1, value=6), CardInfo(type=2, value=2), CardInfo(type=2, value=12),
             CardInfo(type=3, value=4),
             CardInfo(type=3, value=7)],
            [CardInfo(type=3, value=11), CardInfo(type=4, value=12), CardInfo(type=3, value=10),
             CardInfo(type=3, value=1),
             CardInfo(type=3, value=3), CardInfo(type=4, value=5), CardInfo(type=3, value=2), CardInfo(type=3, value=7),
             CardInfo(type=4, value=11)],
            [CardInfo(type=1, value=11), CardInfo(type=4, value=1), CardInfo(type=1, value=13),
             CardInfo(type=2, value=3),
             CardInfo(type=1, value=6), CardInfo(type=2, value=12), CardInfo(type=4, value=4),
             CardInfo(type=4, value=7),
             CardInfo(type=4, value=10)],
            [CardInfo(type=1, value=10), CardInfo(type=1, value=4), CardInfo(type=4, value=11),
             CardInfo(type=1, value=11),
             CardInfo(type=4, value=2), CardInfo(type=2, value=10), CardInfo(type=3, value=10),
             CardInfo(type=2, value=4),
             CardInfo(type=1, value=9)],
            [CardInfo(type=2, value=6), CardInfo(type=3, value=12), CardInfo(type=4, value=13),
             CardInfo(type=3, value=11),
             CardInfo(type=1, value=3), CardInfo(type=3, value=5), CardInfo(type=1, value=6), CardInfo(type=4, value=1),
             CardInfo(type=4, value=4)],
            [CardInfo(type=4, value=11), CardInfo(type=3, value=8), CardInfo(type=2, value=8),
             CardInfo(type=2, value=1),
             CardInfo(type=3, value=1), CardInfo(type=1, value=11), CardInfo(type=1, value=5),
             CardInfo(type=4, value=4),
             CardInfo(type=3, value=9)],
            [CardInfo(type=1, value=8), CardInfo(type=1, value=12), CardInfo(type=1, value=4),
             CardInfo(type=2, value=13),
             CardInfo(type=3, value=6), CardInfo(type=4, value=13), CardInfo(type=3, value=12),
             CardInfo(type=4, value=10),
             CardInfo(type=2, value=9)],
            [CardInfo(type=2, value=12), CardInfo(type=1, value=1), CardInfo(type=2, value=4),
             CardInfo(type=2, value=2),
             CardInfo(type=3, value=10), CardInfo(type=1, value=10), CardInfo(type=3, value=4),
             CardInfo(type=3, value=8),
             CardInfo(type=4, value=6)],
            [CardInfo(type=1, value=9), CardInfo(type=2, value=1), CardInfo(type=2, value=13),
             CardInfo(type=2, value=5),
             CardInfo(type=2, value=11), CardInfo(type=4, value=13), CardInfo(type=1, value=5),
             CardInfo(type=1, value=6),
             CardInfo(type=4, value=4)],
            [CardInfo(type=3, value=12), CardInfo(type=3, value=10), CardInfo(type=4, value=12),
             CardInfo(type=1, value=4),
             CardInfo(type=4, value=9), CardInfo(type=2, value=13), CardInfo(type=3, value=7),
             CardInfo(type=3, value=1),
             CardInfo(type=1, value=11)],
            [CardInfo(type=4, value=7), CardInfo(type=2, value=11), CardInfo(type=4, value=8),
             CardInfo(type=1, value=3),
             CardInfo(type=1, value=11), CardInfo(type=3, value=13), CardInfo(type=2, value=2),
             CardInfo(type=3, value=10),
             CardInfo(type=4, value=1)],
            [CardInfo(type=4, value=11), CardInfo(type=1, value=9), CardInfo(type=2, value=2),
             CardInfo(type=4, value=4),
             CardInfo(type=4, value=10), CardInfo(type=1, value=10), CardInfo(type=3, value=11),
             CardInfo(type=3, value=8),
             CardInfo(type=4, value=8)],
            [CardInfo(type=4, value=5), CardInfo(type=1, value=11), CardInfo(type=1, value=2),
             CardInfo(type=4, value=12),
             CardInfo(type=3, value=11), CardInfo(type=3, value=13), CardInfo(type=4, value=11),
             CardInfo(type=2, value=4),
             CardInfo(type=2, value=10)],
            [CardInfo(type=1, value=9), CardInfo(type=1, value=13), CardInfo(type=2, value=13),
             CardInfo(type=1, value=3),
             CardInfo(type=3, value=2), CardInfo(type=2, value=1), CardInfo(type=4, value=7), CardInfo(type=3, value=9),
             CardInfo(type=1, value=5)],
            [CardInfo(type=4, value=10), CardInfo(type=2, value=12), CardInfo(type=2, value=7),
             CardInfo(type=1, value=10),
             CardInfo(type=4, value=6), CardInfo(type=3, value=12), CardInfo(type=1, value=1),
             CardInfo(type=4, value=12),
             CardInfo(type=1, value=7)],
            [CardInfo(type=3, value=7), CardInfo(type=3, value=2), CardInfo(type=1, value=12),
             CardInfo(type=3, value=10),
             CardInfo(type=3, value=9), CardInfo(type=3, value=6), CardInfo(type=2, value=6),
             CardInfo(type=1, value=13),
             CardInfo(type=2, value=4)],
            [CardInfo(type=1, value=7), CardInfo(type=2, value=8), CardInfo(type=1, value=13),
             CardInfo(type=3, value=6),
             CardInfo(type=3, value=3), CardInfo(type=4, value=8), CardInfo(type=2, value=7), CardInfo(type=2, value=6),
             CardInfo(type=2, value=4)],
            [CardInfo(type=2, value=11), CardInfo(type=3, value=5), CardInfo(type=1, value=6),
             CardInfo(type=4, value=11),
             CardInfo(type=1, value=11), CardInfo(type=4, value=9), CardInfo(type=1, value=13),
             CardInfo(type=1, value=9),
             CardInfo(type=3, value=10)],
            [CardInfo(type=2, value=10), CardInfo(type=1, value=8), CardInfo(type=2, value=1),
             CardInfo(type=4, value=8),
             CardInfo(type=3, value=10), CardInfo(type=4, value=10), CardInfo(type=3, value=3),
             CardInfo(type=2, value=9),
             CardInfo(type=4, value=13)],
            [CardInfo(type=4, value=8), CardInfo(type=2, value=5), CardInfo(type=3, value=1), CardInfo(type=1, value=5),
             CardInfo(type=4, value=3), CardInfo(type=3, value=13), CardInfo(type=2, value=13),
             CardInfo(type=1, value=9),
             CardInfo(type=4, value=12)],
            [CardInfo(type=1, value=10), CardInfo(type=2, value=3), CardInfo(type=3, value=3),
             CardInfo(type=4, value=5),
             CardInfo(type=4, value=8), CardInfo(type=4, value=11), CardInfo(type=4, value=2),
             CardInfo(type=2, value=9),
             CardInfo(type=1, value=1)],
            [CardInfo(type=2, value=12), CardInfo(type=3, value=4), CardInfo(type=2, value=9),
             CardInfo(type=1, value=2),
             CardInfo(type=4, value=4), CardInfo(type=2, value=10), CardInfo(type=4, value=5),
             CardInfo(type=2, value=6),
             CardInfo(type=3, value=12)],
            [CardInfo(type=3, value=4), CardInfo(type=1, value=3), CardInfo(type=4, value=12),
             CardInfo(type=4, value=3),
             CardInfo(type=3, value=8), CardInfo(type=3, value=7), CardInfo(type=2, value=7),
             CardInfo(type=1, value=13),
             CardInfo(type=1, value=5)],
            [CardInfo(type=3, value=9), CardInfo(type=2, value=5), CardInfo(type=1, value=8), CardInfo(type=2, value=3),
             CardInfo(type=4, value=3), CardInfo(type=3, value=5), CardInfo(type=2, value=7),
             CardInfo(type=4, value=11),
             CardInfo(type=1, value=12)],
            [CardInfo(type=4, value=6), CardInfo(type=1, value=5), CardInfo(type=2, value=5), CardInfo(type=3, value=2),
             CardInfo(type=3, value=7), CardInfo(type=4, value=2), CardInfo(type=1, value=6), CardInfo(type=2, value=4),
             CardInfo(type=1, value=12)],
            [CardInfo(type=4, value=10), CardInfo(type=1, value=12), CardInfo(type=3, value=7),
             CardInfo(type=3, value=10),
             CardInfo(type=1, value=13), CardInfo(type=3, value=6), CardInfo(type=1, value=2),
             CardInfo(type=3, value=8),
             CardInfo(type=2, value=8)],
            [CardInfo(type=1, value=12), CardInfo(type=1, value=9), CardInfo(type=4, value=2),
             CardInfo(type=3, value=6),
             CardInfo(type=3, value=3), CardInfo(type=4, value=12), CardInfo(type=2, value=7),
             CardInfo(type=2, value=3),
             CardInfo(type=1, value=4)],
            [CardInfo(type=4, value=4), CardInfo(type=2, value=11), CardInfo(type=1, value=10),
             CardInfo(type=2, value=6),
             CardInfo(type=3, value=6), CardInfo(type=2, value=4), CardInfo(type=1, value=4), CardInfo(type=2, value=8),
             CardInfo(type=4, value=11)],
            [CardInfo(type=4, value=5), CardInfo(type=2, value=9), CardInfo(type=3, value=2),
             CardInfo(type=3, value=11),
             CardInfo(type=2, value=4), CardInfo(type=4, value=1), CardInfo(type=4, value=10),
             CardInfo(type=4, value=8),
             CardInfo(type=2, value=3)],
            [CardInfo(type=1, value=5), CardInfo(type=4, value=9), CardInfo(type=3, value=6), CardInfo(type=2, value=4),
             CardInfo(type=1, value=10), CardInfo(type=4, value=12), CardInfo(type=1, value=2),
             CardInfo(type=1, value=7),
             CardInfo(type=2, value=3)],
            [CardInfo(type=4, value=9), CardInfo(type=4, value=7), CardInfo(type=2, value=6),
             CardInfo(type=3, value=10),
             CardInfo(type=1, value=6), CardInfo(type=4, value=2), CardInfo(type=3, value=8), CardInfo(type=1, value=4),
             CardInfo(type=3, value=7)],
            [CardInfo(type=2, value=11), CardInfo(type=4, value=10), CardInfo(type=3, value=9),
             CardInfo(type=1, value=1),
             CardInfo(type=4, value=5), CardInfo(type=2, value=12), CardInfo(type=3, value=6),
             CardInfo(type=2, value=8),
             CardInfo(type=4, value=11)],
            [CardInfo(type=3, value=3), CardInfo(type=3, value=11), CardInfo(type=2, value=3),
             CardInfo(type=4, value=7),
             CardInfo(type=2, value=7), CardInfo(type=3, value=5), CardInfo(type=1, value=4),
             CardInfo(type=3, value=12),
             CardInfo(type=3, value=8)],
            [CardInfo(type=2, value=1), CardInfo(type=1, value=13), CardInfo(type=1, value=7),
             CardInfo(type=4, value=5),
             CardInfo(type=1, value=8), CardInfo(type=2, value=9), CardInfo(type=2, value=5),
             CardInfo(type=2, value=13),
             CardInfo(type=3, value=12)],
            [CardInfo(type=1, value=13), CardInfo(type=2, value=9), CardInfo(type=1, value=8),
             CardInfo(type=1, value=4),
             CardInfo(type=2, value=6), CardInfo(type=2, value=3), CardInfo(type=2, value=4),
             CardInfo(type=4, value=10),
             CardInfo(type=2, value=11)],
            [CardInfo(type=3, value=13), CardInfo(type=1, value=9), CardInfo(type=1, value=13),
             CardInfo(type=4, value=13),
             CardInfo(type=2, value=7), CardInfo(type=3, value=12), CardInfo(type=3, value=9),
             CardInfo(type=4, value=2),
             CardInfo(type=4, value=4)])

    def get_fake_equal_data(self):
        return (
            [CardInfo(type=1, value=6), CardInfo(type=3, value=8), CardInfo(type=4, value=5), CardInfo(type=4, value=4),
             CardInfo(type=1, value=13), CardInfo(type=3, value=5), CardInfo(type=1, value=4),
             CardInfo(type=4, value=9),
             CardInfo(type=3, value=12)],
            [CardInfo(type=2, value=1), CardInfo(type=2, value=8), CardInfo(type=1, value=10),
             CardInfo(type=3, value=4),
             CardInfo(type=2, value=13), CardInfo(type=4, value=13), CardInfo(type=1, value=13),
             CardInfo(type=2, value=3),
             CardInfo(type=3, value=1)],
            [CardInfo(type=1, value=3), CardInfo(type=4, value=7), CardInfo(type=4, value=5),
             CardInfo(type=2, value=12),
             CardInfo(type=2, value=11), CardInfo(type=4, value=13), CardInfo(type=3, value=13),
             CardInfo(type=1, value=7),
             CardInfo(type=2, value=2)],
            [CardInfo(type=1, value=6), CardInfo(type=3, value=10), CardInfo(type=4, value=7),
             CardInfo(type=3, value=11),
             CardInfo(type=1, value=3), CardInfo(type=3, value=3), CardInfo(type=1, value=7), CardInfo(type=3, value=6),
             CardInfo(type=4, value=5)],
            [CardInfo(type=1, value=3), CardInfo(type=2, value=13), CardInfo(type=3, value=4),
             CardInfo(type=4, value=4),
             CardInfo(type=1, value=7), CardInfo(type=2, value=1), CardInfo(type=1, value=6), CardInfo(type=1, value=5),
             CardInfo(type=1, value=13)],
            [CardInfo(type=1, value=13), CardInfo(type=2, value=4), CardInfo(type=4, value=12),
             CardInfo(type=2, value=9),
             CardInfo(type=1, value=10), CardInfo(type=1, value=1), CardInfo(type=4, value=7),
             CardInfo(type=4, value=13),
             CardInfo(type=1, value=5)],
            [CardInfo(type=4, value=9), CardInfo(type=1, value=3), CardInfo(type=2, value=7),
             CardInfo(type=2, value=10),
             CardInfo(type=1, value=13), CardInfo(type=2, value=8), CardInfo(type=3, value=1),
             CardInfo(type=3, value=9),
             CardInfo(type=4, value=2)],
            [CardInfo(type=3, value=2), CardInfo(type=4, value=7), CardInfo(type=4, value=13),
             CardInfo(type=2, value=8),
             CardInfo(type=4, value=8), CardInfo(type=2, value=1), CardInfo(type=1, value=1),
             CardInfo(type=2, value=10),
             CardInfo(type=4, value=6)],
            [CardInfo(type=2, value=7), CardInfo(type=3, value=4), CardInfo(type=3, value=9),
             CardInfo(type=3, value=12),
             CardInfo(type=2, value=10), CardInfo(type=1, value=9), CardInfo(type=4, value=8),
             CardInfo(type=4, value=2),
             CardInfo(type=3, value=6)],
            [CardInfo(type=3, value=4), CardInfo(type=1, value=9), CardInfo(type=2, value=10),
             CardInfo(type=3, value=5),
             CardInfo(type=4, value=6), CardInfo(type=1, value=3), CardInfo(type=4, value=1), CardInfo(type=2, value=9),
             CardInfo(type=2, value=4)],
            [CardInfo(type=4, value=2), CardInfo(type=1, value=4), CardInfo(type=3, value=2), CardInfo(type=1, value=5),
             CardInfo(type=1, value=11), CardInfo(type=4, value=5), CardInfo(type=2, value=2),
             CardInfo(type=1, value=2),
             CardInfo(type=1, value=12)],
            [CardInfo(type=4, value=5), CardInfo(type=1, value=4), CardInfo(type=4, value=3),
             CardInfo(type=4, value=13),
             CardInfo(type=1, value=13), CardInfo(type=2, value=3), CardInfo(type=4, value=9),
             CardInfo(type=4, value=4),
             CardInfo(type=2, value=8)],
            [CardInfo(type=1, value=2), CardInfo(type=2, value=3), CardInfo(type=3, value=3),
             CardInfo(type=2, value=10),
             CardInfo(type=3, value=6), CardInfo(type=3, value=13), CardInfo(type=4, value=12),
             CardInfo(type=3, value=8),
             CardInfo(type=1, value=3)],
            [CardInfo(type=3, value=3), CardInfo(type=2, value=1), CardInfo(type=4, value=1),
             CardInfo(type=4, value=10),
             CardInfo(type=4, value=13), CardInfo(type=1, value=12), CardInfo(type=2, value=10),
             CardInfo(type=1, value=1),
             CardInfo(type=1, value=8)],
            [CardInfo(type=1, value=8), CardInfo(type=2, value=5), CardInfo(type=4, value=13),
             CardInfo(type=2, value=10),
             CardInfo(type=3, value=6), CardInfo(type=2, value=7), CardInfo(type=4, value=10),
             CardInfo(type=2, value=4),
             CardInfo(type=3, value=8)],
            [CardInfo(type=4, value=4), CardInfo(type=3, value=12), CardInfo(type=3, value=5),
             CardInfo(type=3, value=8),
             CardInfo(type=4, value=5), CardInfo(type=1, value=5), CardInfo(type=3, value=1),
             CardInfo(type=4, value=12),
             CardInfo(type=2, value=6)],
            [CardInfo(type=4, value=1), CardInfo(type=3, value=2), CardInfo(type=2, value=1),
             CardInfo(type=1, value=12),
             CardInfo(type=3, value=13), CardInfo(type=2, value=10), CardInfo(type=3, value=11),
             CardInfo(type=4, value=7),
             CardInfo(type=2, value=4)],
            [CardInfo(type=4, value=5), CardInfo(type=4, value=9), CardInfo(type=4, value=11),
             CardInfo(type=2, value=7),
             CardInfo(type=4, value=2), CardInfo(type=3, value=7), CardInfo(type=1, value=13),
             CardInfo(type=4, value=3),
             CardInfo(type=3, value=9)],
            [CardInfo(type=1, value=4), CardInfo(type=3, value=9), CardInfo(type=1, value=12),
             CardInfo(type=3, value=1),
             CardInfo(type=2, value=1), CardInfo(type=3, value=10), CardInfo(type=1, value=13),
             CardInfo(type=3, value=7),
             CardInfo(type=1, value=5)],
            [CardInfo(type=4, value=3), CardInfo(type=1, value=4), CardInfo(type=2, value=12),
             CardInfo(type=1, value=13),
             CardInfo(type=4, value=9), CardInfo(type=1, value=7), CardInfo(type=2, value=9), CardInfo(type=2, value=4),
             CardInfo(type=3, value=2)],
            [CardInfo(type=2, value=6), CardInfo(type=3, value=11), CardInfo(type=3, value=5),
             CardInfo(type=4, value=7),
             CardInfo(type=1, value=4), CardInfo(type=1, value=2), CardInfo(type=2, value=2),
             CardInfo(type=4, value=11),
             CardInfo(type=1, value=6)],
            [CardInfo(type=3, value=8), CardInfo(type=2, value=3), CardInfo(type=1, value=7), CardInfo(type=3, value=6),
             CardInfo(type=2, value=2), CardInfo(type=2, value=6), CardInfo(type=3, value=2), CardInfo(type=2, value=5),
             CardInfo(type=1, value=8)],
            [CardInfo(type=3, value=2), CardInfo(type=2, value=9), CardInfo(type=4, value=2), CardInfo(type=2, value=4),
             CardInfo(type=4, value=4), CardInfo(type=4, value=10), CardInfo(type=1, value=8),
             CardInfo(type=4, value=3),
             CardInfo(type=2, value=2)],
            [CardInfo(type=1, value=4), CardInfo(type=4, value=6), CardInfo(type=4, value=1), CardInfo(type=1, value=1),
             CardInfo(type=3, value=1), CardInfo(type=2, value=13), CardInfo(type=3, value=13),
             CardInfo(type=4, value=5),
             CardInfo(type=4, value=8)],
            [CardInfo(type=2, value=1), CardInfo(type=3, value=10), CardInfo(type=4, value=3),
             CardInfo(type=2, value=5),
             CardInfo(type=4, value=12), CardInfo(type=3, value=3), CardInfo(type=1, value=5),
             CardInfo(type=2, value=2),
             CardInfo(type=4, value=1)],
            [CardInfo(type=4, value=8), CardInfo(type=2, value=4), CardInfo(type=4, value=6), CardInfo(type=4, value=1),
             CardInfo(type=1, value=6), CardInfo(type=2, value=2), CardInfo(type=3, value=2), CardInfo(type=3, value=9),
             CardInfo(type=3, value=8)],
            [CardInfo(type=1, value=7), CardInfo(type=2, value=2), CardInfo(type=4, value=10),
             CardInfo(type=2, value=13),
             CardInfo(type=3, value=8), CardInfo(type=1, value=12), CardInfo(type=2, value=9),
             CardInfo(type=3, value=7),
             CardInfo(type=4, value=5)],
            [CardInfo(type=4, value=2), CardInfo(type=1, value=12), CardInfo(type=3, value=10),
             CardInfo(type=2, value=11),
             CardInfo(type=1, value=9), CardInfo(type=2, value=8), CardInfo(type=2, value=12),
             CardInfo(type=2, value=6),
             CardInfo(type=4, value=9)],
            [CardInfo(type=2, value=7), CardInfo(type=4, value=9), CardInfo(type=4, value=2), CardInfo(type=2, value=8),
             CardInfo(type=1, value=6), CardInfo(type=1, value=5), CardInfo(type=2, value=10),
             CardInfo(type=3, value=9),
             CardInfo(type=3, value=7)],
            [CardInfo(type=2, value=7), CardInfo(type=3, value=5), CardInfo(type=4, value=1), CardInfo(type=3, value=8),
             CardInfo(type=3, value=12), CardInfo(type=4, value=8), CardInfo(type=2, value=8),
             CardInfo(type=3, value=11),
             CardInfo(type=4, value=9)],
            [CardInfo(type=4, value=8), CardInfo(type=3, value=6), CardInfo(type=2, value=12),
             CardInfo(type=1, value=10),
             CardInfo(type=4, value=13), CardInfo(type=4, value=11), CardInfo(type=2, value=9),
             CardInfo(type=3, value=7),
             CardInfo(type=2, value=2)],
            [CardInfo(type=1, value=9), CardInfo(type=3, value=11), CardInfo(type=3, value=8),
             CardInfo(type=1, value=13),
             CardInfo(type=1, value=7), CardInfo(type=2, value=11), CardInfo(type=1, value=8),
             CardInfo(type=4, value=2),
             CardInfo(type=1, value=11)],
            [CardInfo(type=4, value=6), CardInfo(type=3, value=2), CardInfo(type=1, value=13),
             CardInfo(type=4, value=7),
             CardInfo(type=4, value=10), CardInfo(type=3, value=7), CardInfo(type=2, value=12),
             CardInfo(type=1, value=4),
             CardInfo(type=1, value=2)],
            [CardInfo(type=3, value=7), CardInfo(type=2, value=8), CardInfo(type=2, value=4), CardInfo(type=4, value=4),
             CardInfo(type=3, value=4), CardInfo(type=3, value=1), CardInfo(type=3, value=13),
             CardInfo(type=4, value=2),
             CardInfo(type=1, value=11)],
            [CardInfo(type=1, value=5), CardInfo(type=2, value=1), CardInfo(type=2, value=10),
             CardInfo(type=3, value=7),
             CardInfo(type=1, value=10), CardInfo(type=2, value=4), CardInfo(type=3, value=9),
             CardInfo(type=1, value=1),
             CardInfo(type=1, value=3)],
            [CardInfo(type=4, value=4), CardInfo(type=2, value=11), CardInfo(type=4, value=9),
             CardInfo(type=4, value=10),
             CardInfo(type=3, value=12), CardInfo(type=3, value=4), CardInfo(type=1, value=10),
             CardInfo(type=2, value=4),
             CardInfo(type=1, value=8)],
            [CardInfo(type=2, value=9), CardInfo(type=1, value=5), CardInfo(type=3, value=4), CardInfo(type=4, value=4),
             CardInfo(type=3, value=7), CardInfo(type=3, value=1), CardInfo(type=4, value=10),
             CardInfo(type=1, value=9),
             CardInfo(type=4, value=8)],
            [CardInfo(type=1, value=1), CardInfo(type=4, value=8), CardInfo(type=3, value=3), CardInfo(type=2, value=3),
             CardInfo(type=1, value=11), CardInfo(type=3, value=9), CardInfo(type=3, value=1),
             CardInfo(type=2, value=1),
             CardInfo(type=1, value=7)],
            [CardInfo(type=2, value=2), CardInfo(type=1, value=10), CardInfo(type=1, value=3),
             CardInfo(type=4, value=7),
             CardInfo(type=3, value=7), CardInfo(type=3, value=12), CardInfo(type=1, value=11),
             CardInfo(type=2, value=6),
             CardInfo(type=4, value=10)],
            [CardInfo(type=2, value=5), CardInfo(type=4, value=10), CardInfo(type=3, value=6),
             CardInfo(type=3, value=13),
             CardInfo(type=3, value=4), CardInfo(type=1, value=13), CardInfo(type=2, value=6),
             CardInfo(type=3, value=10),
             CardInfo(type=4, value=8)])

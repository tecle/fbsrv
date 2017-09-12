# coding:utf-8

import unittest
from games.cards import Card, CardInfo
import games.taxas_poker as Poker


class TaxasPokerTest(unittest.TestCase):
    def get_weight(self, *args):
        s = 0
        for i in args:
            s += (s << 4) + i
        return s

    def get_weight3(self, x, y, z):
        return (x << 8) + (y << 4) + z

    def get_weight4(self, m, x, y, z):
        return (m << 12) + (x << 8) + (y << 4) + z

    def get_weight5(self, n, m, x, y, z):
        return (n << 16) + (m << 12) + (x << 8) + (y << 4) + z

    def get_weight2(self, x, y):
        return (x << 4) + y

    def convert_card_str_to_num(self, s):
        x = s.split('_')
        card_type_str = ('', '黑桃', '红桃', '方块', '草花', '小王', '大王')
        return CardInfo(type=card_type_str.index(x[0]), value=int(x[1]))

    def generate_cards(self, *args):
        return [Card.get_card_info(i) for i in args]

    def gen_pub_card_attr(self, *args):
        cds = [self.convert_card_str_to_num(arg) for arg in args]
        return cds

    def gen_player(self, *args):
        cds = [self.convert_card_str_to_num(arg) for arg in args]
        return Poker.TaxasPlayerV2(cds)

    def assertOrigin(self, expect, actual):
        msg = 'expect:{}, actual:{}'.format(expect, actual)
        self.assertEqual(len(expect), len(actual), msg=msg)
        for i, item in enumerate(expect):
            self.assertEqual(item, actual[i], msg=msg)

    def test_royal_flush(self):
        prv = self.gen_player('红桃_12', '红桃_11', '红桃_9', '红桃_10', '红桃_8', '红桃_1', '红桃_13')
        res = prv.solution
        self.assertEqual(Poker.ResultType.RoyalFlush, res.result_type)
        self.assertEqual(14, res.weight)
        self.assertOrigin([14], res.origin)

        # 全部公共牌
        prv = self.gen_player('红桃_12', '红桃_11', '红桃_1', '红桃_10', '红桃_13', '黑桃_1', '黑桃_13')
        res = prv.solution
        self.assertEqual(Poker.ResultType.RoyalFlush, res.result_type)
        self.assertEqual(14, res.weight)
        self.assertOrigin([14], res.origin)

    def test_flush(self):
        prv = self.gen_player('红桃_10', '红桃_11', '方块_11', '黑桃_11', '红桃_12', '红桃_9', '红桃_13')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Flush, res.result_type)
        self.assertEqual(13, res.weight)
        self.assertEqual((13,), res.origin)

    def test_four(self):
        prv = self.gen_player('红桃_10', '草花_9', '方块_9', '黑桃_11', '红桃_1', '红桃_9', '黑桃_9')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Four, res.result_type)
        self.assertEqual((9 << 4) + 14, res.weight)
        self.assertEqual((9, 1), res.origin)

    def test_gourd(self):
        # A A , A B B D D
        prv = self.gen_player('红桃_10', '草花_9', '方块_10', '黑桃_11', '红桃_11', '红桃_9', '黑桃_9')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Gourd, res.result_type)
        self.assertEqual((9 << 4) + 11, res.weight)

        # A A , A B C D D
        prv = self.gen_player('红桃_10', '草花_9', '方块_7', '黑桃_11', '红桃_11', '红桃_9', '黑桃_9')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Gourd, res.result_type)
        self.assertEqual((9 << 4) + 11, res.weight)

        # A A , D B C D D
        prv = self.gen_player('红桃_10', '草花_9', '方块_11', '黑桃_11', '红桃_11', '红桃_9', '黑桃_9')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Gourd, res.result_type)
        self.assertEqual((11 << 4) + 9, res.weight)

        # A B, A B B D D
        prv = self.gen_player('方块_2', '草花_3', '方块_3', '黑桃_11', '红桃_11', '红桃_2', '黑桃_3')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Gourd, res.result_type)
        self.assertEqual((3 << 4) + 11, res.weight)
        self.assertOrigin([3, 11], res.origin)

        # A B, A B B D E
        prv = self.gen_player('方块_2', '草花_3', '红桃_3', '红桃_11', '红桃_7', '红桃_2', '黑桃_3')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Gourd, res.result_type)
        self.assertEqual((3 << 4) + 2, res.weight)

        # A B, C C C D D
        prv = self.gen_player('方块_6', '草花_6', '红桃_6', '红桃_7', '方块_7', '红桃_4', '黑桃_3')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Gourd, res.result_type)
        self.assertOrigin([6, 7], res.origin)

    def test_same_color(self):
        # 同花 & 高牌
        prv = self.gen_player('红桃_1', '草花_9', '红桃_8', '方块_6', '红桃_7', '红桃_2', '红桃_5')
        res = prv.solution
        self.assertEqual(Poker.ResultType.SameColor, res.result_type)
        self.assertOrigin([1, 8, 7, 5, 2], res.origin)
        # 同花 & 对子
        prv = self.gen_player('红桃_1', '草花_3', '红桃_5', '红桃_11', '红桃_7', '红桃_4', '红桃_3')
        res = prv.solution
        self.assertEqual(Poker.ResultType.SameColor, res.result_type)
        self.assertOrigin([1, 11, 7, 5, 4], res.origin)

        # 同花 & 两对
        prv = self.gen_player('红桃_1', '草花_3', '红桃_5', '草花_4', '红桃_7', '红桃_4', '红桃_3')
        res = prv.solution
        self.assertEqual(Poker.ResultType.SameColor, res.result_type)
        self.assertOrigin([1, 7, 5, 4, 3], res.origin)

        # 同花 & 三条
        prv = self.gen_player('红桃_1', '草花_3', '红桃_5', '方块_3', '红桃_7', '红桃_4', '红桃_3')
        res = prv.solution
        self.assertEqual(Poker.ResultType.SameColor, res.result_type)
        self.assertOrigin([1, 7, 5, 4, 3], res.origin)

        # 同花 & 顺子
        prv = self.gen_player('红桃_1', '草花_2', '红桃_5', '方块_6', '红桃_7', '红桃_4', '红桃_3')
        res = prv.solution
        self.assertEqual(Poker.ResultType.SameColor, res.result_type)
        self.assertOrigin([1, 7, 5, 4, 3], res.origin)

    def test_sequence(self):
        # 顺子 & 高牌
        prv = self.gen_player('方块_3', '草花_5', '红桃_6', '方块_8', '红桃_9', '红桃_4', '黑桃_2')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Sequence, res.result_type)
        self.assertEqual(6, res.weight)

        # 顺子 & 对子
        prv = self.gen_player('方块_3', '草花_5', '红桃_6', '方块_8', '红桃_8', '红桃_4', '黑桃_2')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Sequence, res.result_type)
        self.assertEqual(6, res.weight)

        # 顺子 & 两对
        prv = self.gen_player('方块_3', '草花_5', '红桃_6', '方块_2', '草花_4', '红桃_4', '黑桃_2')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Sequence, res.result_type)
        self.assertEqual(6, res.weight)

        # 顺子 & 三条
        prv = self.gen_player('方块_3', '草花_5', '红桃_6', '方块_2', '红桃_2', '红桃_4', '黑桃_2')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Sequence, res.result_type)
        self.assertEqual(6, res.weight)

        # 顺子 & 只用部分私有牌
        prv = self.gen_player('方块_3', '草花_5', '红桃_6', '方块_4', '红桃_7', '红桃_8', '黑桃_2')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Sequence, res.result_type)
        self.assertOrigin((8, ), res.origin)

        # 顺子 & 全部公共牌
        prv = self.gen_player('方块_3', '草花_5', '红桃_6', '方块_4', '红桃_7', '红桃_1', '黑桃_2')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Sequence, res.result_type)
        self.assertOrigin((7,), res.origin)

    def test_three(self):
        # A A, A B C D E
        prv = self.gen_player('方块_3', '草花_4', '红桃_6', '方块_2', '红桃_1', '红桃_4', '黑桃_4')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Three, res.result_type)
        self.assertOrigin([4, 1, 6], res.origin)

        # A B, A A C D E
        prv = self.gen_player('方块_4', '草花_4', '红桃_6', '方块_2', '红桃_1', '红桃_4', '黑桃_3')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Three, res.result_type)
        self.assertOrigin([4, 1, 6], res.origin)

        # A B, C C C D E
        prv = self.gen_player('方块_6', '草花_6', '红桃_6', '红桃_7', '方块_8', '红桃_4', '黑桃_3')
        res = prv.solution
        self.assertEqual(Poker.ResultType.Three, res.result_type)
        self.assertOrigin([6, 8, 7], res.origin)

    def test_two_pair(self):
        # A A, B B C D E
        prv = self.gen_player('方块_6', '草花_6', '红桃_8', '红桃_7', '方块_9', '红桃_4', '黑桃_4')
        res = prv.solution
        self.assertEqual(Poker.ResultType.TwoPair, res.result_type)
        self.assertEqual([6, 4, 9], res.origin)

        # A B, A B C D E
        prv = self.gen_player('方块_1', '草花_4', '红桃_8', '红桃_7', '方块_9', '红桃_4', '黑桃_1')
        res = prv.solution
        self.assertEqual(Poker.ResultType.TwoPair, res.result_type)
        self.assertOrigin((1, 4, 9), res.origin)

        # A B, A C C D E
        prv = self.gen_player('方块_6', '草花_6', '红桃_4', '红桃_7', '方块_8', '红桃_4', '黑桃_9')
        res = prv.solution
        self.assertEqual(Poker.ResultType.TwoPair, res.result_type)
        self.assertOrigin((6, 4, 9), res.origin)

        # A B, A B C C E
        prv = self.gen_player('方块_6', '草花_6', '红桃_4', '红桃_7', '方块_9', '红桃_4', '黑桃_9')
        res = prv.solution
        self.assertEqual(Poker.ResultType.TwoPair, res.result_type)
        self.assertOrigin((9, 6, 7), res.origin)

    def test_single_pair(self):
        # A B, A C D E F
        prv = self.gen_player('方块_6', '草花_4', '红桃_3', '红桃_7', '方块_8', '红桃_4', '黑桃_9')
        res = prv.solution
        self.assertEqual(Poker.ResultType.SinglePair, res.result_type)
        self.assertEqual(self.get_weight4(4, 9, 8, 7), res.weight)
        self.assertEqual([4, 9, 8, 7], res.origin)

        # A B, C C D E F
        prv = self.gen_player('方块_6', '草花_6', '红桃_3', '红桃_7', '方块_8', '红桃_4', '黑桃_9')
        res = prv.solution
        self.assertEqual(Poker.ResultType.SinglePair, res.result_type)
        self.assertOrigin([6, 9, 8, 7], res.origin)

        # A A, B C D E F
        prv = self.gen_player('方块_6', '草花_1', '红桃_3', '红桃_7', '方块_8', '红桃_4', '黑桃_4')
        res = prv.solution
        self.assertEqual(Poker.ResultType.SinglePair, res.result_type)
        self.assertOrigin([4, 1, 8, 7], res.origin)

    def test_high(self):
        prv = self.gen_player('方块_6', '草花_1', '红桃_12', '红桃_7', '方块_8', '红桃_4', '黑桃_3')
        res = prv.solution
        self.assertEqual(Poker.ResultType.HighCard, res.result_type)
        self.assertEqual(self.get_weight5(14, 12, 8, 7, 6), res.weight)
        self.assertOrigin([1, 12, 8, 7, 6], res.origin)

    def test_abnormal(self):
        prv = self.gen_player('草花_7', '黑桃_10', '红桃_6', '方块_10', '红桃_2', '红桃_4', '草花_5')
        self.assertEqual(Poker.ResultType.SinglePair, prv.solution.result_type)

    def test_run(self):
        game = Poker.TaxasGame()
        result = game.play_game()
        print result.detail
        print game.serialize_game_result(result)

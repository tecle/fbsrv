# coding: utf-8

import unittest
from games.cards import Card
from games.zhajinhua import ZJHPlayer, ZJHResultType, ZhaJinHua


class ZhaJinHuaTest(unittest.TestCase):
    def test_ZJHPlayer(self):
        # 豹子
        t1 = ZJHPlayer([Card.get_card_info(1), Card.get_card_info(1), Card.get_card_info(1)])
        self.assertEqual(ZJHResultType.Leopard, t1.solution)

        # 同花顺
        t2 = ZJHPlayer([Card.get_card_info(4), Card.get_card_info(2), Card.get_card_info(3)])
        self.assertEqual(ZJHResultType.SameColorSeq, t2.solution)

        t2 = ZJHPlayer([Card.get_card_info(1), Card.get_card_info(2), Card.get_card_info(0)])
        self.assertEqual(ZJHResultType.SameColorSeq, t2.solution)
        self.assertEqual((1 << 8) + (3 << 4) + 2, t2.card_weight)

        # 同花
        t3 = ZJHPlayer([Card.get_card_info(4), Card.get_card_info(2), Card.get_card_info(5)])
        self.assertEqual(ZJHResultType.SameColor, t3.solution)

        # 顺子
        t4 = ZJHPlayer([Card.get_card_info(16), Card.get_card_info(2), Card.get_card_info(30)])
        self.assertEqual(ZJHResultType.Seq, t4.solution)

        t4 = ZJHPlayer([Card.get_card_info(14), Card.get_card_info(2), Card.get_card_info(26)])
        self.assertEqual(ZJHResultType.Seq, t4.solution)

        # 对子
        t5 = ZJHPlayer([Card.get_card_info(17), Card.get_card_info(4), Card.get_card_info(37)])
        self.assertEqual(ZJHResultType.Pair, t5.solution)

        # 单张
        t6 = ZJHPlayer([Card.get_card_info(17), Card.get_card_info(10), Card.get_card_info(37)])
        self.assertEqual(ZJHResultType.Single, t6.solution)

    def test_ZhaJinHua_compare_cards_with_diff_solution(self):
        t1 = ZJHPlayer([Card.get_card_info(0), Card.get_card_info(13), Card.get_card_info(26)])  # leopard
        t2 = ZJHPlayer([Card.get_card_info(4), Card.get_card_info(2), Card.get_card_info(3)])  # same color seq
        zjh = ZhaJinHua()
        self.assertTrue(zjh.compare_cards(t1, t2) > 0)

    def test_ZhaJinHua_compare_cards_with_leopard(self):
        zjh = ZhaJinHua()
        # 豹子, 点数不同
        for i in range(1, 13):
            t1 = ZJHPlayer([Card.get_card_info(i), Card.get_card_info(i + 26), Card.get_card_info(i + 13)])
            self.assertEqual(ZJHResultType.Leopard, t1.solution)
            t2 = ZJHPlayer([Card.get_card_info(0), Card.get_card_info(13), Card.get_card_info(26)])
            self.assertEqual(ZJHResultType.Leopard, t2.solution)
            self.assertTrue(zjh.compare_cards(t1, t2) < 0, msg='\n[%s]\n vs \n[%s]' % (t1, t2))

    def test_ZhaJinHua_compare_cards_with_same_color_seq(self):
        zjh = ZhaJinHua()
        # check 同花顺:AKQ A23 234 JQK
        t1 = ZJHPlayer([Card.get_card_info(2), Card.get_card_info(3), Card.get_card_info(1)])  # 234
        t2 = ZJHPlayer([Card.get_card_info(10), Card.get_card_info(12), Card.get_card_info(11)])  # JQK
        t3 = ZJHPlayer([Card.get_card_info(0), Card.get_card_info(11), Card.get_card_info(12)])  # AKQ
        t4 = ZJHPlayer([Card.get_card_info(0), Card.get_card_info(2), Card.get_card_info(1)])  # A23
        ts = [t1, t2, t3, t4]
        ts.sort(cmp=lambda l, r: zjh.compare_cards(l, r), reverse=True)
        self.assertEqual([t3, t2, t1, t4], ts, msg='\n%s' % '\n'.join([str(item) for item in ts]))

        # 牌型相同, 点数相同, 比较花色
        t1 = ZJHPlayer([Card.get_card_info(2), Card.get_card_info(3), Card.get_card_info(1)])  # 234
        t2 = ZJHPlayer([Card.get_card_info(10 + 13), Card.get_card_info(12 + 13), Card.get_card_info(11 +13)])  # JQK
        self.assertEqual(ZJHResultType.SameColorSeq, t1.solution)
        self.assertEqual(ZJHResultType.SameColorSeq, t2.solution)
        self.assertTrue(zjh.compare_cards(t1, t2) < 0)

    def test_ZhaJinHua_compare_cards_with_same_color(self):
        zjh = ZhaJinHua()

        weight_count = [set(), 0]
        t2 = ZJHPlayer([Card.get_card_info(12), Card.get_card_info(10), Card.get_card_info(0)])
        self.assertEqual(ZJHResultType.SameColor, t2.solution)
        t3 = ZJHPlayer([Card.get_card_info(1), Card.get_card_info(4), Card.get_card_info(2)])
        self.assertEqual(ZJHResultType.SameColor, t3.solution)

        for i in range(0, 13):
            for j in range(0, 13):
                if i == j:
                    continue
                for k in range(0, 14):
                    if (k == i or k == j) or not i > j > k:
                        continue
                    if i == 12 and j == 10 and k == 0:
                        continue
                    if i == 4 and j == 2 and k == 1:
                        continue
                    t1 = ZJHPlayer([Card.get_card_info(i), Card.get_card_info(j), Card.get_card_info(k)])
                    if t1.solution != ZJHResultType.SameColor:
                        continue
                    weight_count[0].add(t1.card_weight)
                    weight_count[1] += 1
                    self.assertTrue(zjh.compare_cards(t1, t2) < 0, msg='\n[%s]\n vs \n[%s]' % (t1, t2))
                    self.assertTrue(zjh.compare_cards(t1, t3) > 0, msg='\n[%s]\n vs \n[%s]' % (t1, t3))
        self.assertEqual(len(weight_count[0]), weight_count[1])

    def test_ZhaJinHua_compare_cards_with_seq(self):
        zjh = ZhaJinHua()
        # 顺子:AKQ A23 234 JQK
        t1 = ZJHPlayer([Card.get_card_info(15), Card.get_card_info(3), Card.get_card_info(1)])  # 234
        t2 = ZJHPlayer([Card.get_card_info(23), Card.get_card_info(12), Card.get_card_info(37)])  # JQK
        t3 = ZJHPlayer([Card.get_card_info(13), Card.get_card_info(11), Card.get_card_info(12)])  # AKQ
        t4 = ZJHPlayer([Card.get_card_info(0), Card.get_card_info(15), Card.get_card_info(1)])  # A23
        ts = [t1, t2, t3, t4]
        ts.sort(cmp=lambda l, r: zjh.compare_cards(l, r), reverse=True)
        self.assertEqual([t3, t2, t1, t4], ts, msg='actual:\n%s' % '\n'.join([str(i) for i in ts]))

    def test_ZhaJinHua_compare_cards_with_pair(self):
        zjh = ZhaJinHua()
        weight_count = [set(), 0]
        t2 = ZJHPlayer([Card.get_card_info(13), Card.get_card_info(0), Card.get_card_info(12)])
        self.assertEqual(ZJHResultType.Pair, t2.solution)
        t3 = ZJHPlayer([Card.get_card_info(1), Card.get_card_info(14), Card.get_card_info(2)])
        self.assertEqual(ZJHResultType.Pair, t3.solution)
        # check all pairs
        for i in range(0, 13):
            for j in range(0, 13):
                if i == j or (i == 0 and j == 12) or (i == 1 and j == 2):
                    continue
                t1 = ZJHPlayer([Card.get_card_info(i), Card.get_card_info(i + 13), Card.get_card_info(j)])
                self.assertEqual(ZJHResultType.Pair, t1.solution)
                weight_count[0].add(t1.card_weight)
                weight_count[1] += 1
                self.assertTrue(zjh.compare_cards(t1, t2) < 0, msg='\n[%s]\n vs \n[%s]' % (t1, t2))
                self.assertTrue(zjh.compare_cards(t1, t3) > 0, msg='\n[%s]\n vs \n[%s]' % (t1, t3))
        self.assertEqual(len(weight_count[0]), weight_count[1])

        # 对子的特殊情况: 922 < 887
        t1 = ZJHPlayer([Card.get_card_info(8), Card.get_card_info(1), Card.get_card_info(1 + 13)]) # 922
        t2 = ZJHPlayer([Card.get_card_info(9 + 13), Card.get_card_info(8), Card.get_card_info(9)])# 887
        self.assertTrue(zjh.compare_cards(t1, t2) < 0, msg='\n[%s]\n vs \n[%s]' % (t1, t2))

        # 牌型相同, 点数相同,　比较花色 AAK
        t2 = ZJHPlayer([Card.get_card_info(0 + 39), Card.get_card_info(0), Card.get_card_info(12 + 13)])
        t1 = ZJHPlayer([Card.get_card_info(0 + 13), Card.get_card_info(0 + 26), Card.get_card_info(12)])
        self.assertTrue(zjh.compare_cards(t1, t2) < 0, msg='\n[%s]\n vs \n[%s]' % (t1, t2))

        # 牌型相同, 点数相同,　比较花色 AKK
        t2 = ZJHPlayer([Card.get_card_info(12 + 39), Card.get_card_info(0), Card.get_card_info(12 + 36)])
        t1 = ZJHPlayer([Card.get_card_info(12 + 13), Card.get_card_info(0 + 26), Card.get_card_info(12)])
        self.assertTrue(zjh.compare_cards(t1, t2) > 0, msg='\n[%s]\n vs \n[%s]' % (t1, t2))

    def test_ZhaJinHua_compare_cards_with_single(self):
        zjh = ZhaJinHua()
        t1 = ZJHPlayer([Card.get_card_info(6), Card.get_card_info(16), Card.get_card_info(10)])
        self.assertEqual(ZJHResultType.Single, t1.solution)
        t2 = ZJHPlayer([Card.get_card_info(13), Card.get_card_info(12), Card.get_card_info(10)])
        self.assertEqual(ZJHResultType.Single, t2.solution)
        t3 = ZJHPlayer([Card.get_card_info(2), Card.get_card_info(17), Card.get_card_info(1)])
        self.assertEqual(ZJHResultType.Single, t3.solution)
        self.assertTrue(zjh.compare_cards(t2, t3) > 0, msg='\n[%s]\n vs \n[%s]' % (t2, t3))
        self.assertTrue(zjh.compare_cards(t2, t1) > 0, msg='\n[%s]\n vs \n[%s]' % (t2, t1))
        self.assertTrue(zjh.compare_cards(t3, t1) < 0, msg='\n[%s]\n vs \n[%s]' % (t3, t1))

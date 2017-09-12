# coding: utf-8

import logging
import games.game_base as GameBase
from games.fake_result_factory import FakeTaxasResult


class ResultType(object):
    HighCard = 1  # 高牌
    SinglePair = 2  # 对子
    TwoPair = 3  # 两对
    Three = 4  # 三条
    Sequence = 5  # 顺子
    SameColor = 6  # 同花
    Gourd = 7  # 葫芦
    Four = 8  # 四条
    Flush = 9  # 同花顺
    RoyalFlush = 10  # 皇家同花顺


ResultTypeStr = ('', '高牌', '对子', '两对', '三条', '顺子', '同花', '葫芦', '四条', '同花顺', '皇家同花顺')


class TaxasSolution(object):
    def __init__(self, t, w):
        self.result_type = t
        self.origin = w
        factor = (0, 4, 8, 12, 16)
        s = 0
        for i, www in enumerate(reversed(w)):
            s += ((www if www > 1 else 14) << factor[i])
        self.weight = s

    def __lt__(self, other):
        if self.result_type != other.result_type:
            return self.result_type - other.result_type < 0
        return self.weight - other.weight < 0

    def __gt__(self, other):
        if self.result_type != other.result_type:
            return self.result_type - other.result_type > 0
        return self.weight - other.weight > 0

    def __eq__(self, other):
        if self.result_type != other.result_type:
            return False
        return self.weight == other.weight

    def __ne__(self, other):
        return not self.__eq__(other)

    def serialize(self):
        return ResultTypeStr[self.result_type]

    def __str__(self):
        out = [
            'weight is {0}'.format(self.weight),
            '牌型为:{0}'.format(ResultTypeStr[self.result_type]),
            '组合为:{0}'.format(self.origin)
        ]
        return '\n'.join(out)


class TaxasPlayerV2(GameBase.CardPlayer):
    def __init__(self, cds):
        super(TaxasPlayerV2, self).__init__(cds)

    def init_data(self):
        self.cards.sort(cmp=GameBase.get_card_cmp_func(1), reverse=True)

    def find_best_solution(self):
        max_seq_num = 1
        seq_start_val = self.cards[0].value
        pre = None
        # pairs 和 thirds 存的是该对子或三张的牌值
        pairs = []
        thirds = []
        four = None
        same_count = 1
        card_types = [[], [], [], [], []]
        for card in self.cards:
            val = card.value
            card_types[card.type].append(val)
            if pre:
                if pre == val:
                    # 对子情况
                    same_count += 1
                    if same_count == 2:
                        pairs.append(val)
                    elif same_count == 3:
                        pairs.pop()
                        thirds.append(val)
                    elif same_count == 4:
                        four = val
                        break
                else:
                    # 与前面一张牌值不同
                    same_count = 1
                    if max_seq_num < 5:
                        # 没有组成序列
                        diff = pre - val
                        if diff == 1 or diff == -12:
                            # 顺子情况, 3 -> 2 or A -> k
                            max_seq_num += 1
                        else:
                            # 无法构成序列时重置数据
                            seq_start_val = val
                            max_seq_num = 1
            pre = val
        if four:
            # 找到最大的单牌
            for item in self.cards:
                if item.value != four:
                    return TaxasSolution(ResultType.Four, (four, item.value))
        same_color = None
        for card_list in card_types:
            if len(card_list) > 4:
                same_color = card_list
                break
        # same_color = [card1, card2, ...]
        if same_color and max_seq_num > 4:
            # 判断是否是同花, 相同颜色的已经排好队在same_color中了
            idx = 1
            ng_count = 0
            header = pre = same_color[0] if same_color[0] > 1 else 14
            while idx < len(same_color):
                val = same_color[idx] if same_color[idx] > 1 else 14
                if pre - val == 1:
                    ng_count += 1
                else:
                    ng_count = 1
                    header = val
                if ng_count == 4:
                    break
                idx += 1
                pre = val
            if ng_count >= 4:
                return TaxasSolution(ResultType.RoyalFlush if header == 14 else ResultType.Flush, (header,))
        if thirds:
            if len(thirds) == 2:
                return TaxasSolution(ResultType.Gourd, (thirds[0], thirds[1]))
            if pairs:
                return TaxasSolution(ResultType.Gourd, (thirds[0], pairs[0]))
        if same_color:
            return TaxasSolution(ResultType.SameColor, same_color[:5])
        if max_seq_num > 4:
            return TaxasSolution(ResultType.Sequence, (seq_start_val,))
        if thirds:
            thirds_val = thirds[0]
            flag = [thirds_val]
            for item in self.cards:
                if item.value != thirds_val:
                    flag.append(item.value)
                    if len(flag) == 3:
                        break
            # 再找两个散牌
            return TaxasSolution(ResultType.Three, flag)
        if len(pairs) > 1:
            pair_tag = [pairs[0], pairs[1]]
            for item in self.cards:
                val = item.value
                if val not in pair_tag:
                    pair_tag.append(val)
                    break
            # 使用前两对, 再找一个大散牌
            return TaxasSolution(ResultType.TwoPair, pair_tag)
        elif len(pairs) == 1:
            pair_tag = [pairs[0]]
            for item in self.cards:
                val = item.value
                if val != pairs[0]:
                    pair_tag.append(val)
                    if len(pair_tag) == 4:
                        break
            return TaxasSolution(ResultType.SinglePair, pair_tag)
        return TaxasSolution(ResultType.HighCard, [self.cards[i].value for i in range(0, 5)])


class TaxasGame(GameBase.CardGameBase):
    def __init__(self):
        super(TaxasGame, self).__init__()

    def play_game(self, winner_slot=None):
        '''
        :param winner_slot: 0. left win; 1. equal; 2. right win
        :return:返回结果中把牌返回[LL,MMMMM,RR]一共9张牌
        '''
        cds = self.shuffle_52(1, 9)[0]
        player1 = TaxasPlayerV2(cds[:7])
        player2 = TaxasPlayerV2(cds[-7:])
        winner_idx = \
            0 if player1.solution > player2.solution else (2 if player1.solution < player2.solution else 1)
        if winner_slot is None or winner_idx == winner_slot:
            players = (player1, player2, cds)
            return GameBase.CommonGameResult(
                result_list=players, winner_index=winner_idx, detail=self.convert_result(players))
        if winner_slot == 1:
            # 要求二者大小相等，实际是两者不相等
            # 生成两个相等的玩家后返回
            logging.debug('fake data with equal:%s', winner_slot)
            return _fake_data_.get_result(1)
        if winner_idx == 1:
            # 要求二者不相等，实际是两者相等
            logging.debug('fake data with not equal:%s', winner_slot)
            return _fake_data_.get_result(winner_slot)
        # 要求二者不相等, 而且赢家位置相反, 交换玩家位置后返回
        cds[0], cds[-1] = cds[-1], cds[0]
        cds[1], cds[-2] = cds[-2], cds[1]
        players = (player2, player1, cds)
        return GameBase.CommonGameResult(
            result_list=players, winner_index=winner_slot, detail=self.convert_result(players))

    @staticmethod
    def convert_result(players):
        cards = players[2]
        return {
            GameBase.GameCardsStr: [
                {
                    GameBase.GameCardTypeStr: card.type,
                    GameBase.GameCardValueStr: card.value
                }
                for card in cards
                ],
            GameBase.GameCardSpecialStr: [players[0].solution.result_type, players[1].solution.result_type]
        }

    def get_slot_count(self):
        return 3

    def serialize_game_result(self, result):
        return '{}|{};{}|{}'.format(
            result.winner_index,
            result.result_list[0].solution.serialize(),
            result.result_list[1].solution.serialize(),
            self.str_cards(result.result_list[2])
        )

    def str_cards(self, card_list):
        return ','.join(['%s_%d' % (card.type, card.value) for card in card_list])


_fake_data_ = FakeTaxasResult(TaxasGame, TaxasPlayerV2)

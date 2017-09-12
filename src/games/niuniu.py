# coding: utf-8

from games.cards import CardNum
from games.game_base import CardGameBase
from games.game_base import CardPlayer
from games.game_base import compare_single_card
from games.game_base import CommonGameResult
from collections import namedtuple

NiuNiuResult = namedtuple('NiuNiuResult', ['result_list', 'winner_index'])


class NiuNiuResultType(object):
    Niu0 = 0  # 无牛
    Niu1 = 1  # 牛N
    Niu2 = 2
    Niu3 = 3
    Niu4 = 4
    Niu5 = 5
    Niu6 = 6
    Niu7 = 7
    Niu8 = 8
    Niu9 = 9
    NiuNiu = 10
    BigCow = 11  # 五花牛
    TinyCow = 12  # 五小牛
    FourBomb = 13  # 四炸


def map_value(card_value):
    '''
    :param card_value: card.CardInfo
    '''
    if card_value > CardNum.Card_10:
        return 10
    return card_value


class NiuNiuPlayer(CardPlayer):
    __slots__ = []

    def __init__(self, cards):
        '''
        :param cards: [card.CardInfo,...]
        '''
        super(NiuNiuPlayer, self).__init__(cards)

    def init_data(self):
        self.cards.sort(cmp=compare_single_card, key=lambda item: item, reverse=True)

    def find_best_solution(self):
        '''
        :param cards: [card.CardInfo, card.CardInfo, ...]
        :return: NiuNIuResultType
        '''
        card_value_sum = 0
        card_value_list = []
        # 预处理
        for card in self.cards:
            val = map_value(card.value)
            card_value_sum += val
            card_value_list.append(val)

        # 初始没牛, 穷举
        max_sum_3, max_remain = 0, 0
        for first in range(5):
            for second in range(first + 1, 5):
                for third in range(second + 1, 5):
                    sum_3 = card_value_list[first] + card_value_list[second] + card_value_list[third]
                    if sum_3 % 10 != 0:
                        continue
                    cur_remain = (card_value_sum - sum_3) % 10
                    if cur_remain == 0:
                        return NiuNiuResultType.NiuNiu
                    if cur_remain > max_remain:
                        max_sum_3, max_remain = sum_3, cur_remain
        if max_sum_3 == 0:
            return NiuNiuResultType.Niu0
        return max_remain

    def __str__(self):
        card_type_str = ('', '黑桃', '红桃', '方块', '草花', '小王', '大王')
        solution_str = ('没牛', '牛一', '牛二', '牛三', '牛四', '牛五', '牛六', '牛七', '牛八', '牛九',
                        '牛牛', '四炸', '五花牛', '五小牛')
        out = []
        for card in self.cards:
            out.append('%s_%d' % (card_type_str[card.type], card.value))
        out.append(solution_str[self.solution])
        return ','.join(out)


class NiuNiuGameBase(CardGameBase):
    def __init__(self):
        super(NiuNiuGameBase, self).__init__()

    def compare_cards(self, left, right):
        '''
        :param left: NiuNiuPlayer
        :param right: NiuNiuPlayer
        :return: positive digit if left bigger than right , otherwise positive digit. and no chance for equal.
        '''
        if left.solution == right.solution:
            for i, item in enumerate(left.cards):
                return compare_single_card(item, right.cards[i])
        return left.solution - right.solution

    def sort_result(self, result):
        '''
        :param result: [NiuNiuPlayer, ...]
        :return: sorted [NiuNiuPlayer, ...]
        '''
        result.sort(cmp=self.compare_cards, key=lambda key: key, reverse=True)

    def get_slot_count(self):
        return 3


class NiuNiuFor2Player(NiuNiuGameBase):
    '''
    param for play_game:
    bet id: 0, left win; 1, equal; 2, right win
    CommonGameResult.result_list=[left NiuNiuPlayer, right NiuNiuPlayer]
    CommonGameResult.winner_index=winner index in bet_info
    '''

    def __init__(self):
        super(NiuNiuFor2Player, self).__init__()

    def generate_players(self):
        pass

    def play_game(self, winner_slot=None):
        '''
        :param winner_slot: 0, left win; 1, equal; 2, right win
        '''
        tmp = [NiuNiuPlayer(cs) for cs in self.shuffle_52(2, 5)]
        if not winner_slot:
            winner_slot = 0 if tmp[0].solution > tmp[1].solution else (2 if tmp[0].solution < tmp[1].solution else 1)
            return CommonGameResult(result_list=tmp, winner_index=winner_slot, detail=self.convert_result(tmp))
        if winner_slot < 1:
            players = tmp if tmp[0].solution > tmp[1].solution else (tmp[1], tmp[0])
            return CommonGameResult(result_list=players, winner_index=winner_slot,detail=self.convert_result(players))
        elif winner_slot > 1:
            players = tmp if tmp[0].solution < tmp[1].solution else (tmp[1], tmp[0])
            return CommonGameResult(result_list=players,winner_index=winner_slot, detail=self.convert_result(players))
        return self.generate_fake_equal_result()

    @staticmethod
    def generate_fake_equal_result():
        raise NotImplementedError()


class NiuNiuFor3Player(NiuNiuGameBase):
    def __init__(self):
        super(NiuNiuFor3Player, self).__init__()

    def generate_players(self):
        return [NiuNiuPlayer(cs) for cs in self.shuffle_52(3, 5)]

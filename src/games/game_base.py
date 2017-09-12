# coding: utf-8

import random
from games.cards import Card
from games.cards import CardType
from games.cards import CardNum
from collections import namedtuple

CommonGameResult = namedtuple('CommonGameResult', ['result_list', 'winner_index', 'detail'])

GameCardsStr = 'CD'
GameCardTypeStr = 'T'
GameCardValueStr = 'V'
GameCardSpecialStr = 'S'
GameBetListStr = 'BL'


def get_card_cmp_func(offset):
    def func(left, right):
        return to_real_card_value(left.value, offset) - to_real_card_value(right.value, offset)

    return func


def to_real_card_value(value, offset):
    return value if value > offset else value + CardNum.Card_K


def compare_single_card(left, right, offset=0,
                        card_type_order=(CardType.Diamond, CardType.Club, CardType.Heart, CardType.Spade)):
    '''
    :param left: card.CardInfo
    :param right: card.CardInfo
    :param offset: 计算牌点数大小时的偏移量, 比如偏移量为1时, A最大
    :param card_type_order: 花色大小排序, 从小到大
    :return positive: left > right; 0: left == right; negative: left < right
    '''
    if left.type == right.type:
        return to_real_card_value(left.value, offset) - to_real_card_value(right.value, offset)
    return card_type_order.index(left.type) - card_type_order.index(right.type)


class CommonPlayer(object):
    __slots__ = []

    def __init__(self):
        pass

    def serialize(self):
        raise NotImplementedError()


class CardPlayer(CommonPlayer):
    __slots__ = ['cards', 'solution']

    def __init__(self, cards):
        '''
        :param cards: [card.CardInfo,...]
        '''
        super(CardPlayer, self).__init__()
        self.cards = cards
        self.init_data()
        self.solution = self.find_best_solution()

    def init_data(self):
        pass

    def find_best_solution(self):
        '''
        :param cards: [card.CardInfo, card.CardInfo, ...]
        :return: bet solution tag
        '''
        raise NotImplementedError()

    def serialize(self):
        return ','.join(['%s_%d' % (card.type, card.value) for card in self.cards])

    def __str__(self):
        card_type_str = ('', '黑桃', '红桃', '方块', '草花', '小王', '大王')
        out = []
        for card in self.cards:
            out.append('%s_%d' % (card_type_str[card.type], card.value))
        return ','.join(out)


class CommonGameBase(object):
    def __init__(self):
        self.status = None

    def set_game_status(self, new_status):
        self.status = new_status

    def play_game(self, winner_slot=None):
        '''
        :param winner_slot: 获胜者的位置, 如果为None则是内部生成
        :return: CommonGameResult
        '''
        players = self.generate_players()
        winner_idx = self.get_winner_index(players)
        if winner_slot is None or winner_idx == winner_slot:
            return CommonGameResult(result_list=players, winner_index=winner_idx, detail=self.convert_result(players))
        players[winner_idx], players[winner_slot] = players[winner_slot], players[winner_idx]
        return CommonGameResult(result_list=players, winner_index=winner_slot, detail=self.convert_result(players))

    def generate_players(self):
        raise NotImplementedError()

    def get_slot_count(self):
        raise NotImplementedError()

    def get_winner_index(self, results):
        raise NotImplementedError()

    @staticmethod
    def convert_result(players):
        '''convert game result to json object, mostly it will saved to CommonGameResult.detail .'''
        raise NotImplementedError()

    def serialize_game_result(self, result):
        '''Serialize game result that will save to MySQL.'''
        # CommonGameResult = namedtuple('CommonGameResult', ['result_list', 'winner_index', 'detail'])
        return '{}|{}'.format(result.winner_index, ';'.join(player.serialize() for player in result.result_list))


class CardGameBase(CommonGameBase):
    def __init__(self):
        super(CardGameBase, self).__init__()

    @staticmethod
    def shuffle_52(player_num, card_num):
        '''
        shuffle cards without jokers.
        :param player_num:...
        :return: [five cards for player0, five cards for player1...]
        '''
        card_seq = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
                    27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51)
        ret = random.sample(card_seq, player_num * card_num)
        return [[Card.get_card_info(ret[j]) for j in range(i * card_num, (i + 1) * card_num)]
                for i in range(player_num)]

    def get_winner_index(self, results):
        '''
        get winner index
        :param results: [CardPlayer, ...]
        :return: winner index in game results
        '''
        max_index = 0
        for i, item in enumerate(results):
            if self.compare_cards(results[max_index], item) < 0:
                max_index = i
        return max_index

    def compare_cards(self, left, right):
        raise NotImplementedError()

    @staticmethod
    def convert_result(players):
        return [{
                    GameCardsStr: [
                        {
                            GameCardTypeStr: card.type,
                            GameCardValueStr: card.value
                        }
                        for card in player.cards
                        ],
                    GameCardSpecialStr: player.solution
                } for player in players]

    def serialize_game_result(self, result):
        # CommonGameResult = namedtuple('CommonGameResult', ['result_list', 'winner_index', 'detail'])
        return '{}|{}'.format(result.winner_index, ';'.join(player.serialize() for player in result.result_list))

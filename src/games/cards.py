# coding: utf-8

# [0, 12]黑桃(A->K)
# [13, 25]红桃(A->K)
# [26, 38]方块(A->K)
# [39, 51]草花(A->K)
# 52 小王
# 53 大王
# 以上为一副牌, 下副牌的起始值为 52(不要大小王), 54(要大小王)

from collections import namedtuple


def card_weight_2(x, y):
    return (x << 4) + y


def card_weight_3(x, y, z):
    return (x << 8) + (y << 4) + z


def card_weight_4(m, x, y, z):
    return (m << 12) + (x << 8) + (y << 4) + z


class CardType(object):
    Spade = 1  # 黑桃
    Heart = 2  # 红桃
    Diamond = 3  # 方块
    Club = 4  # 草花
    BlackJoker = 5  # 小王
    RedJoker = 6  # 大王
    Sentinel = 7  # 哨兵类型，表示最大的那个类型的整型值


class CardNum(object):
    Card_A = 1
    Card_2 = 2
    Card_3 = 3
    Card_4 = 4
    Card_5 = 5
    Card_6 = 6
    Card_7 = 7
    Card_8 = 8
    Card_9 = 9
    Card_10 = 10
    Card_J = 11
    Card_Q = 12
    Card_K = 13
    Card_BlackJoker = 2 * Card_K + 1  # 这里是为了解决牌点比较时大小鬼的问题
    Card_RedJoker = 2 * Card_K + 2


CardInfo = namedtuple('CardInfo', ['type', 'value'])


class Card(object):
    CardMapping = (
        CardInfo(CardType.Spade, CardNum.Card_A),
        CardInfo(CardType.Spade, CardNum.Card_2),
        CardInfo(CardType.Spade, CardNum.Card_3),
        CardInfo(CardType.Spade, CardNum.Card_4),
        CardInfo(CardType.Spade, CardNum.Card_5),
        CardInfo(CardType.Spade, CardNum.Card_6),
        CardInfo(CardType.Spade, CardNum.Card_7),
        CardInfo(CardType.Spade, CardNum.Card_8),
        CardInfo(CardType.Spade, CardNum.Card_9),
        CardInfo(CardType.Spade, CardNum.Card_10),
        CardInfo(CardType.Spade, CardNum.Card_J),
        CardInfo(CardType.Spade, CardNum.Card_Q),
        CardInfo(CardType.Spade, CardNum.Card_K),
        CardInfo(CardType.Heart, CardNum.Card_A),
        CardInfo(CardType.Heart, CardNum.Card_2),
        CardInfo(CardType.Heart, CardNum.Card_3),
        CardInfo(CardType.Heart, CardNum.Card_4),
        CardInfo(CardType.Heart, CardNum.Card_5),
        CardInfo(CardType.Heart, CardNum.Card_6),
        CardInfo(CardType.Heart, CardNum.Card_7),
        CardInfo(CardType.Heart, CardNum.Card_8),
        CardInfo(CardType.Heart, CardNum.Card_9),
        CardInfo(CardType.Heart, CardNum.Card_10),
        CardInfo(CardType.Heart, CardNum.Card_J),
        CardInfo(CardType.Heart, CardNum.Card_Q),
        CardInfo(CardType.Heart, CardNum.Card_K),
        CardInfo(CardType.Diamond, CardNum.Card_A),
        CardInfo(CardType.Diamond, CardNum.Card_2),
        CardInfo(CardType.Diamond, CardNum.Card_3),
        CardInfo(CardType.Diamond, CardNum.Card_4),
        CardInfo(CardType.Diamond, CardNum.Card_5),
        CardInfo(CardType.Diamond, CardNum.Card_6),
        CardInfo(CardType.Diamond, CardNum.Card_7),
        CardInfo(CardType.Diamond, CardNum.Card_8),
        CardInfo(CardType.Diamond, CardNum.Card_9),
        CardInfo(CardType.Diamond, CardNum.Card_10),
        CardInfo(CardType.Diamond, CardNum.Card_J),
        CardInfo(CardType.Diamond, CardNum.Card_Q),
        CardInfo(CardType.Diamond, CardNum.Card_K),
        CardInfo(CardType.Club, CardNum.Card_A),
        CardInfo(CardType.Club, CardNum.Card_2),
        CardInfo(CardType.Club, CardNum.Card_3),
        CardInfo(CardType.Club, CardNum.Card_4),
        CardInfo(CardType.Club, CardNum.Card_5),
        CardInfo(CardType.Club, CardNum.Card_6),
        CardInfo(CardType.Club, CardNum.Card_7),
        CardInfo(CardType.Club, CardNum.Card_8),
        CardInfo(CardType.Club, CardNum.Card_9),
        CardInfo(CardType.Club, CardNum.Card_10),
        CardInfo(CardType.Club, CardNum.Card_J),
        CardInfo(CardType.Club, CardNum.Card_Q),
        CardInfo(CardType.Club, CardNum.Card_K),
        CardInfo(CardType.BlackJoker, CardNum.Card_BlackJoker),
        CardInfo(CardType.RedJoker, CardNum.Card_RedJoker),
    )

    @staticmethod
    def get_card_info(index, with_joker=False):
        factor = 54 if with_joker else 52
        num = index % factor
        return Card.CardMapping[num]


if __name__ == '__main__':
    card = Card.get_card_info(108, True)
    print card.type
    print card.value

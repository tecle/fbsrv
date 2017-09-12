# coding: utf-8

from games.game_base import to_real_card_value
from games.cards import CardType, CardNum
from games.game_base import CardGameBase
from games.game_base import CardPlayer
from games.game_base import CommonGameResult


class ZJHResultType(object):
    Single = 0  # 单张
    Pair = 1  # 对子
    Seq = 2  # 顺子
    SameColor = 3  # 同花
    SameColorSeq = 4  # 同花顺
    Leopard = 5  # 豹子


class ZJHPlayer(CardPlayer):
    __slots__ = ['card_real_value', 'card_weight']

    def __init__(self, cards):
        self.card_real_value = None
        self.card_weight = 0
        super(ZJHPlayer, self).__init__(cards)
        if len(cards) != 3:
            raise Exception('Invalid card number, expected: 3, current: %s' % len(cards))

    def init_data(self):
        self.cards.sort(cmp=lambda l, r: to_real_card_value(l, 1) - to_real_card_value(r, 1),
                        key=lambda item: item.value, reverse=True)
        self.card_real_value = (
            to_real_card_value(self.cards[0].value, 1),
            to_real_card_value(self.cards[1].value, 1),
            to_real_card_value(self.cards[2].value, 1),
        )

        # 特征值计算: x, y, z -> x * 16 * 16 + y * 16 + z, 确保每种牌型不同点数的特征值都不一样
        # 对子的特征值需要另外计算: x, x, y -> x * 16 + y
        # 顺子的特征值需要进行纠正
        self.card_weight = (self.card_real_value[0] << 8) + (self.card_real_value[1] << 4) + self.card_real_value[2]

    def find_best_solution(self):
        big, middle, small = self.card_real_value
        differ_0 = big - middle
        differ_1 = middle - small
        same_color = self.cards[0].type == self.cards[1].type == self.cards[2].type
        if differ_0 == differ_1:
            if not differ_0:
                return ZJHResultType.Leopard
            if differ_0 == 1:
                return ZJHResultType.SameColorSeq if same_color else ZJHResultType.Seq
        if differ_0 == 11 and middle == CardNum.Card_3 and small == CardNum.Card_2:
            # 特殊情况: 顺子A 2 3, 纠正权重
            self.card_weight -= (13 << 8)
            return ZJHResultType.SameColorSeq if same_color else ZJHResultType.Seq
        if same_color:
            return ZJHResultType.SameColor
        if differ_0 == 0:
            # AAB
            self.card_weight = (middle << 4) + small
        elif differ_1 == 0:
            # ABB
            self.card_weight = (middle << 4) + big
        else:
            return ZJHResultType.Single
        return ZJHResultType.Pair

    def __str__(self):
        card_type_str = ('', '黑桃', '红桃', '方块', '草花', '小王', '大王')
        solution_str = ('单张', '对子', '顺子', '同花', '同花顺', '豹子')
        out = []
        for card in self.cards:
            out.append('%s_%d' % (card_type_str[card.type], card.value))
        out.append(solution_str[self.solution])
        out.append(str(self.card_weight))
        return ','.join(out)


class ZhaJinHua(CardGameBase):
    def __init__(self):
        super(ZhaJinHua, self).__init__()
        self.card_type_order = [0] * CardType.Sentinel
        self.card_type_order[CardType.Diamond] = 0
        self.card_type_order[CardType.Club] = 1
        self.card_type_order[CardType.Heart] = 2
        self.card_type_order[CardType.Spade] = 3
        self.max_card_type = max(self.card_type_order, key=lambda k: self.card_type_order[k])

    def generate_players(self):
        return [ZJHPlayer(i) for i in self.shuffle_52(3, 3)]

    def compare_cards(self, left, right):
        if left.solution != right.solution:
            return left.solution - right.solution
        tmp = left.card_weight - right.card_weight
        if tmp != 0:
            return tmp
        l_head, r_head = left.cards[0], right.cards[0]
        if left.solution == ZJHResultType.Pair and l_head.value == left.cards[1].value:
            # 对子的花色比较: AAB 和ABB两种情况, 只有前者需要特殊处理
            if l_head.type == self.max_card_type or left.cards[1].type == self.max_card_type:
                return 1
            return -1
        # 如果是相同的牌型, 那么第一个n元素的花色一定不相同
        return self.card_type_order[l_head.type] - self.card_type_order[r_head.type]

    def get_slot_count(self):
        return 3

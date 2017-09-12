# coding: utf-8

import random
from collections import namedtuple

WinnerRateConfig = namedtuple('WinnerRateConfig', ['max_rate', 'rate_list'])


class Decider001(object):
    def __init__(self, lose_limit, multiple_rate):
        # 这个应该是从配置中读取,
        # 1, 确保是有序的
        # 2, 确保最后一项的max_rate足够大
        # 3, rate_list中的配置对应的是下注从小到大的概率
        self.winner_rate = [
            WinnerRateConfig(max_rate=0.6, rate_list=(0.48, 0.27, 0.25)),
            WinnerRateConfig(max_rate=0.8, rate_list=(0.47, 0.28, 0.25)),
            # WinnerRateConfig(max_rate=1.0, rate_list=(0.25, 0.29, 0.46)),
            # WinnerRateConfig(max_rate=1.2, rate_list=(0.25, 0.29, 0.46)),
            WinnerRateConfig(max_rate=1.5, rate_list=(0.46, 0.29, 0.25)),
            # WinnerRateConfig(max_rate=2.0, rate_list=(0.25, 0.30, 0.45)),
            WinnerRateConfig(max_rate=100000, rate_list=(0.45, 0.30, 0.25)),
        ]
        self.lose_limit = lose_limit
        self.multiple_rate = multiple_rate

    def decide_winner(self, bet_info, bet_in, bet_out):
        '''
        注意: 本函数会对传入的bet_info进行原地排序
        :param bet_info: [(bet_id, bet_val), (bet_id, bet_val), ...]当前下注情况
        :param bet_in: 24h内总下注
        :param bet_out: 24h内总产出
        :return: 获胜者在bet_info中的索引值
        '''
        bet_info.sort(key=lambda x: x[1])
        # 排序后, 最大的在最后一个
        earn_rate = float(bet_in) / bet_out
        earned = bet_in - bet_out
        fw, idx = self.force_win(bet_info, earned)
        if fw:
            return idx
        rate_config = None
        for item in self.winner_rate:
            if earn_rate > item.max_rate:
                continue
            rate_config = item
            break
        if rate_config is None:
            # 如果没有找到配置, 则总是押最小的获胜
            return 0
        sed = random.randint(0, 1000) / 1000.0
        helper = 0.0
        for i, rate in enumerate(rate_config.rate_list):
            helper += rate
            if sed < helper:
                return i
        # 如果概率配置错误, 则押最小者获胜
        return 0

    def force_win(self, bet_info, earned):
        '''
        :param bet_info: 排序后的bet_info, 最大的在最后一个, 确保bet_info的长度为3
        :param earned: 净赚
        :return: 是否强制获胜 bool, 获胜者在bet_info中的索引值
        '''
        bet_A = bet_info[-1][1]
        if bet_A * self.multiple_rate > earned and bet_A >= self.lose_limit:
            bet_B = bet_info[-2][1]
            if bet_B * self.multiple_rate > earned and bet_B >= self.lose_limit:
                return True, 0
            else:
                return True, random.choice((0, 1))
        return False, None

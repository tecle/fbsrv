# coding: utf-8

import json
import logging

from utils.util_tools import parse_reward_in_json_obj


class LoginRewardConfig(object):
    __slots__ = ['cfg', 'max_reward']

    def __init__(self):
        self.cfg = {}
        self.max_reward = []

    def parse_from_json_file(self, path):
        try:
            with open(path) as f:
                obj = json.loads(f.read())
                max_day = 0
                for item in obj['login reward config']:
                    self.cfg[item['day']] = []
                    parse_reward_in_json_obj(item['reward'], self.cfg[item['day']])
                    if len(self.cfg[item['day']]) == 0:
                        raise Exception('no reward provided.')
                    max_day = max(max_day, item['day'])
                self.max_reward = self.cfg[max_day]
        except Exception:
            logging.exception('parse login reward config failed:[%s]')
            return False
        return True

    def reward_for_day(self, day):
        '''
        in version 1, all reward is gold. so this function will just return first reward item.
        :param day:
        :return: reward_type, gold_amount
        '''
        if day == 0:
            return 0, 0
        if day not in self.cfg:
            return self.max_reward[0]
        return self.cfg[day][0]

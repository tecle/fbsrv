# coding: utf-8

import json
import logging

from utils.util_tools import parse_reward_in_json_obj


class CreditsLevelConfig(object):
    __slots__ = ['level', 'credits_need', 'reward']

    def __init__(self, level, credits_need, reward):
        self.level = level
        self.credits_need = credits_need
        self.reward = []
        parse_reward_in_json_obj(reward, self.reward)


class CreditsConfig(object):
    __slots__ = ['cfg']

    def __init__(self):
        self.cfg = {}

    def credits_need_for_level(self, level):
        if level not in self.cfg:
            return None
        return self.cfg[level].credits_need

    def get_credits_level_reward(self, level):
        if level not in self.cfg:
            return None
        return self.cfg[level].reward

    def parse_from_json_file(self, path):
        '''
        :param path: config file path
        :return: parse result(bool)
        '''
        try:
            config_str = None
            with open(path) as f:
                config_str = f.read()
            obj = json.loads(config_str)
            for item in obj['credits config']:
                config_item = CreditsLevelConfig(item['level'], item['credits need'], item['reward'])
                self.cfg[item['level']] = config_item
        except Exception, e:
            logging.exception('Parse credits config failed.')
            return False
        return True

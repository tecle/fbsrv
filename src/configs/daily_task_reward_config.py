# coding: utf-8

import json

from utils.common_define import RewardType
from utils.common_define import TaskType
from utils.util_tools import parse_reward_in_json_obj


class DailyTaskRewardConfig(object):
    def __init__(self):
        self.data = {}

    def parse_from_json_file(self, path):
        with open(path) as f:
            obj = json.loads(f.read())
            for task_type in dir(TaskType):
                if task_type.startswith('__') or task_type not in obj:
                    continue
                type_id = getattr(TaskType, task_type)
                self.data[type_id] = {}
                for task_detail in obj[task_type]:
                    self.data[type_id][task_detail['count']] = []
                    parse_reward_in_json_obj(task_detail['reward'], self.data[type_id][task_detail['count']])
                    if len(task_detail['reward']) == 0:
                        raise Exception('No reward for task[%s].' % task_type)

    def get_task_reward(self, task_type, task_data):
        '''
        :param task_type:
        :param task_data:
        :return: gain reward(bool), reward value((reward type, reward value))
        '''
        if task_type not in self.data or task_data not in self.data[task_type]:
            return False, (RewardType.NoReward, 0)
        return True, self.data[task_type][task_data][0]

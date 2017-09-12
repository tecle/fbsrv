# coding: utf-8

import datetime

from utils.common_define import TaskType


class DailyTaskData(object):
    __slots__ = [
        'task_data',
        'task_date'
    ]

    def __init__(self):
        self.task_data = [0] * TaskType.TypeNumber
        self.task_date = datetime.date.today()

    def reset_count(self):
        self.task_data = [0] * TaskType.TypeNumber

    def check_new_day(self):
        t = datetime.date.today()
        new_day = (t - self.task_date).days != 0
        if new_day:
            self.task_date = t
            self.reset_count()
        return new_day

    def update_task_data(self, task_type, increment_value=1):
        '''
        increment task data at position of task_type by increment_value
        :param task_type: TaskType.*
        :param increment_value: int
        :return: current value
        '''
        self.check_new_day()
        self.task_data[task_type] += increment_value
        return self.task_data[task_type]

    def get_tasks_data(self, task_types):
        '''
        get tasks data info specified by task_types
        :param task_types: [TaskType.type1, TaskType.type2, ...]
        :return: [data1, data2, ...]
        '''
        return [self.task_data[i] for i in task_types]

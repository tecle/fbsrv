# coding: utf-8

import unittest
from controller.user_resource_define import DailyTaskData, TaskType
import datetime


class DailyTaskDataTest(unittest.TestCase):

    def test_check_new_day_not_new_day(self):
        obj = DailyTaskData()
        obj.task_date = datetime.datetime.now().date()
        obj.task_data[TaskType.Login] = 1
        self.assertFalse(obj.check_new_day())
        self.assertEqual(1, obj.task_data[TaskType.Login])

    def test_check_new_day(self):
        obj = DailyTaskData()
        obj.task_date = datetime.date(2016, 12, 6)
        obj.task_data[TaskType.Login] = 1
        self.assertTrue(obj.check_new_day())
        self.assertEqual(0, obj.task_data[TaskType.Login])

    def test_check_attribute(self):
        obj = DailyTaskData()
        try:
            obj.task_date = None
            obj.attr_not_exist = 1
            self.assertEqual(1, 0)
        except Exception, e:
            self.assertEqual(AttributeError, type(e))

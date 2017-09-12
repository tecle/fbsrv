# coding: utf-8

import unittest

from controller.daily_task_manager import DailyTaskManager
from controller.user_resource_define import DailyTaskData, TaskType


class FakeCache(object):

    def __init__(self):
        self.data = None

    def increment_user_credits(self, *args):
        self.data = args

    def get_cache(self, name):
        return self


class FakeSettings(object):
    def __init__(self):
        pass


class DailyTaskManagerTest(unittest.TestCase):
    def setUp(self):
        DailyTaskManager.user_tasks.clear()

    def tearDown(self):
        DailyTaskManager.user_tasks.clear()

    def test_pub_active_user_not_exist(self):
        cache = FakeCache()
        settings = FakeSettings()
        settings.publish_reward = 2
        settings.publish_reward_max = 10
        obj = DailyTaskManager(cache, settings)
        self.assertEqual(0, len(DailyTaskManager.user_tasks))
        self.assertEqual((1, 2), obj.pub_active(1))
        self.assertTrue(1 in DailyTaskManager.user_tasks)
        self.assertEqual(1, DailyTaskManager.user_tasks[1].task_data[TaskType.PublishActive])

    def test_pub_active_user_exist(self):
        cache = FakeCache()
        settings = FakeSettings()
        settings.publish_reward = 2
        settings.publish_reward_max = 10

        record = DailyTaskData()
        DailyTaskManager.user_tasks[1] = record
        record.update_task_data(TaskType.PublishActive)

        obj = DailyTaskManager(cache, settings)
        self.assertEqual(1, len(DailyTaskManager.user_tasks))
        self.assertEqual((2, 2), obj.pub_active(1))
        self.assertTrue(1 in DailyTaskManager.user_tasks)
        self.assertEqual(2, DailyTaskManager.user_tasks[1].task_data[TaskType.PublishActive])
        self.assertIsNotNone(cache.data)
        self.assertEqual((1, 2), cache.data)

    def test_pub_active_user_not_increment_credits(self):
        cache = FakeCache()
        settings = FakeSettings()
        settings.publish_reward = 2
        settings.publish_reward_max = 10

        record = DailyTaskData()
        DailyTaskManager.user_tasks[1] = record
        record.update_task_data(TaskType.PublishActive, 5)

        obj = DailyTaskManager(cache, settings)
        self.assertEqual((6, 0), obj.pub_active(1))
        self.assertEqual(6, DailyTaskManager.user_tasks[1].task_data[TaskType.PublishActive])
        self.assertIsNone(cache.data)


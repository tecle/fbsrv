# coding: utf-8

import logging

from controller.user_resource_define import DailyTaskData
from model.cache.user_res_cache import UserResCache
from utils.common_define import TaskType


class DailyTaskManager(object):
    user_tasks = {}

    def __init__(self, cache, settings):
        self.cache = cache
        self.settings = settings

    def get_user_task_data(self, uid):
        if uid not in self.user_tasks:
            self.user_tasks[uid] = DailyTaskData()
        return self.user_tasks[uid]

    def reward_wrapper(self, uid, task_type, reward, reward_max, comment):
        count = self.get_user_task_data(uid).update_task_data(task_type)
        if reward * count > reward_max:
            return count, 0
        logging.info('user[%d] get [%d] credits by [%s].' % (uid, reward, comment))
        self.cache.get_cache(UserResCache.cache_name).increment_user_credits(uid, reward)
        return count, reward

    def pub_active(self, uid):
        return self.reward_wrapper(uid, TaskType.PublishActive, self.settings.publish_reward,
                                   self.settings.publish_reward_max, 'publish active')

    def comment_someone(self, uid):
        return self.reward_wrapper(uid, TaskType.CommentSomeone, self.settings.comment_reward,
                                   self.settings.comment_reward_max, 'comment someone')

    def chat_with_someone(self, uid):
        return self.reward_wrapper(uid, TaskType.ChatWithSomeone, self.settings.chat_reward,
                                   self.settings.chat_reward_max, 'chat with someone')

    def watch_live(self, uid):
        return self.reward_wrapper(uid, TaskType.WatchLive, self.settings.watch_reward,
                                   self.settings.watch_reward_max, 'watch live')

    def login(self, uid):
        return self.reward_wrapper(uid, TaskType.Login, self.settings.login_reward,
                                   self.settings.login_reward_max, 'login')

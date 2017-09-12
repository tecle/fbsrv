# coding: utf-8


class ServerResource(object):
    def __init__(self):
        self.config = None
        self.redis = None
        self.async_im = None
        self.async_live = None
        self.active_cache = None
        self.user_detail_cache = None
        self.daily_task = None


    def get_cache(self, name):
        return self.redis.get_cache(name)

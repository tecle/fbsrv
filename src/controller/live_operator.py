# coding: utf-8

import logging

import tornado.gen
import tornado.ioloop

import celeryapp.tasks as CeleryTasks
import model.roommessage as LiveMessage
from model.cache import LiveCache
from model.cache import UserResCache
from utils.common_define import ErrorCode


class BaseProcessor(object):
    def __init__(self, cache_wrapper):
        self.live_cache = cache_wrapper.get_cache(LiveCache.cache_name)
        self.user_res_cache = cache_wrapper.get_cache(UserResCache.cache_name)

    def process(self, uid, lid, msg):
        '''
        :return: response_str, broadcast_str
        '''
        raise NotImplementedError()


class LiveManager(object):
    def __init__(self, cache_wrapper, qiniu_api, gift_conf):
        self.live_cache = cache_wrapper.get_cache(LiveCache.cache_name)
        self.user_res_cache = cache_wrapper.get_cache(UserResCache.cache_name)
        self.qiniu = qiniu_api
        self.processor = {}
        self.lives_data = {}
        self.timer = None
        self.io_loop = tornado.ioloop.IOLoop.current()
        self.gift_conf = gift_conf

    def handle_send_gift_event(self, user_id, target_id, gift_id, number):
        # 先确定是否是重复请求, 如果是, 则直接返回结果
        cost = self.gift_conf.get_gift_cost(gift_id)
        if not cost:
            logging.warning('user %d send gift to %d failed: gifts not exist.' % (user_id, target_id))
            return ErrorCode.NotExist, None, None
        total = cost * number
        success, detail = self.user_res_cache.send_gift_to_living_girl(user_id, user_id, total)
        gold_remain, live_charm = detail[0], detail[1]
        if not success:
            logging.warning('user %d send gift to %d failed with lack money.' % (user_id, target_id))
            return ErrorCode.ResourceError, None, None
        # save send gift record to db.
        try:
            CeleryTasks.send_gift.apply_async(args=(user_id, gift_id, target_id, total, number))
        except:
            logging.exception('celery task for usr %s send %s to usr %s failed.'.format(user_id, gift_id, target_id))
        return 0, gold_remain, live_charm

    def handle_start_live_event(self, uid, channel_info=None, chat_room_info=None):
        if not channel_info and not chat_room_info:
            self.live_cache.add_user_to_living_list(uid)
        else:
            self.live_cache.update_live_settings(uid, channel_info, chat_room_info)

    def handle_close_live_event(self, uid, req_type):
        self.live_cache.close_live(uid)
        # self.io_loop.add_callback(partial(self.notify_user_live_closed, uid))
        return LiveMessage.format_close_live_response(True, req_type)

    @tornado.gen.coroutine
    def notify_user_live_closed(self, live_id):
        # todo: 异步通知聊天室成员直播xxx已经关闭
        pass

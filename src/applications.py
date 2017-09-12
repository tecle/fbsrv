# coding :utf-8

import datetime
import logging
import tornado.web


class CommonApplication(tornado.web.Application):
    def __init__(self, routine_table, **settings):
        self.cargo_conf = None
        self.server_conf = None
        self.app_conf = None

        self.user_center = None
        self.ground_center = None
        self.ali_pay = None
        self.wx_pay = None
        self.qiniu_api = None
        self.secure_tools = None

        self.redis_wrapper = None
        self.db_conn = None

        self.async_im = None
        self.async_live = None

        self.game_manager = None
        self.game_conf = None
        self.socket_manager = None
        self.live_biz = None
        self.daily_task_biz = None
        self.growth_system = None
        self.host_ctrl = None
        self.watcher_ctrl = None
        self.rpc = None

        self.actives_cache = None
        self.user_detail_cache = None

        self.tecent_access_tool = None

        self.num_processed_requests = 0
        self.num_watcher_conns = 0
        self.num_live_conns = 0

        self.srv_start_time = 0
        self.srv_stop_time = 0
        super(CommonApplication, self).__init__(routine_table, **settings)

    def get_cache(self, cache_name):
        return self.redis_wrapper.get_cache(cache_name)

    def summary(self):
        self.srv_stop_time = datetime.datetime.now()
        logging.info('>>>>>> Total processed request: %s', self.num_processed_requests)
        logging.info('>>>>>> Total accepted host websockets: %s', self.num_live_conns)
        logging.info('>>>>>> Total accepted watcher websockets: %s', self.num_watcher_conns)
        logging.info('>>>>>> Start time: %s, End time: %s', self.srv_start_time, self.srv_stop_time)
        logging.info('>>>>>> Runtime: %s', self.srv_stop_time - self.srv_stop_time)

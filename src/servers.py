# coding: utf-8

import os

import handlers.operation_handler as OpHandlers
from applications import CommonApplication
from routing_table import ROUTING_TABLE, OP_TABLE, LIVE_TABLE, DB_TABLE
from server_base import ServerBase
from utils.rpcfrmwrk import RpcHandler


class ExpApplication(CommonApplication):
    def __init__(self, routine_table, **settings):
        super(ExpApplication, self).__init__(routine_table, **settings)
        self.host_ctrl = None
        self.watcher_ctrl = None
        self.rpc = None


class GameLogicServer(ServerBase):
    def __init__(self, *args):
        super(GameLogicServer, self).__init__(*args)
        self.init_celery_client()

    def init_app(self):
        handlers = self.get_routine_table()
        self.app = ExpApplication(handlers)
        self.init_app_attr()

    @staticmethod
    def get_routine_table():
        return [
            (r'/exp/rpc/game', RpcHandler),
            (r'/live/freeze', OpHandlers.GameFreezingHandler),
        ]

    def init_app_attr(self):
        self.app.redis_wrapper = self.get_redis_wrapper()
        self.init_config_sync_thread(self.app.redis_wrapper.r.pubsub())
        self.app.server_conf = self.server_cfg
        game_conf = self.get_game_config()
        self.app.game_manager = self.get_game_manager(game_conf, self.app.redis_wrapper)


class LogicServer(ServerBase):
    '''
    功能:
    1,用户模块的业务逻辑
    2,广场/动态模块的业务逻辑
    3,支付模块(待拆分)
    '''

    def __init__(self, *args):
        super(LogicServer, self).__init__(*args)
        self.init_celery_client()

    def init_app(self):
        self.init_db_conn_pool()
        handlers = self.get_routine_table()
        self.app = CommonApplication(handlers)
        self.init_app_attr()

    def init_app_attr(self):
        self.app.redis_wrapper = self.get_redis_wrapper()
        self.app.async_im = self.get_async_im()
        self.init_config_sync_thread(self.app.redis_wrapper.r.pubsub())
        self.app.user_center = self.get_user_center(self.app.redis_wrapper.r, self.app.async_im)
        self.app.ground_center = self.get_ground_center(self.app.redis_wrapper)

        self.app.app_conf = self.get_app_config(self.app.redis_wrapper.r)
        self.app.cargo_conf = self.app.app_conf.cargo_conf_inst
        self.app.server_conf = self.server_cfg
        self.app.ali_pay = self.get_ali_pay_api()
        self.app.wx_pay = self.get_wx_pay_api()
        self.app.qiniu_api = self.get_qiniu_api()
        self.app.secure_tools = self.get_secure_tools()
        self.app.db_conn = self.get_db_conn()
        self.app.async_db = self.get_async_db()
        self.app.async_live = self.get_async_live()
        self.app.tecent_access_tool = self.get_tecent_access_tool()

        game_conf = self.get_game_config()
        self.app.game_manager = self.get_game_manager(game_conf, self.app.redis_wrapper)
        gift_conf = self.get_gift_config()
        self.app.live_biz = self.get_live_biz(self.app.redis_wrapper, self.app.qiniu_api, gift_conf)
        self.app.daily_task_biz = self.get_daily_task(self.app.redis_wrapper)
        self.app.actives_cache = self.get_active_cache()
        self.app.user_detail_cache = self.get_user_detail_cache()

    @staticmethod
    def get_routine_table():
        from handlers.common_handler import ReportHeartbeatHandler
        return ROUTING_TABLE + [('/heartbeat/report', ReportHeartbeatHandler)] + OP_TABLE


class LiveServer(LogicServer):
    @staticmethod
    def get_routine_table():
        return LIVE_TABLE

    def init_app_attr(self):
        self.app.redis_wrapper = self.get_redis_wrapper()
        self.init_config_sync_thread(self.app.redis_wrapper.r.pubsub())
        self.init_game_sync_thread(self.app.redis_wrapper.r.pubsub())
        self.app.rpc = self.get_game_rpc()
        self.app.host_ctrl = self.get_host_ctrl(self.app.redis_wrapper)
        self.app.watcher_ctrl = self.get_watcher_ctrl()

        self.app.server_conf = self.server_cfg
        self.app.qiniu_api = self.get_qiniu_api()
        self.app.async_im = self.get_async_im()
        self.app.async_live = self.get_async_live()
        self.app.game_conf = self.get_game_config()

        gift_conf = self.get_gift_config()
        self.app.live_biz = self.get_live_biz(self.app.redis_wrapper, self.app.qiniu_api, gift_conf)


class PayServer(ServerBase):
    def __init__(self, *args):
        super(PayServer, self).__init__(*args)
        self.init_celery_client()

    def init_app(self):
        from routing_table import PAY_TABLE

        self.app = CommonApplication(PAY_TABLE)
        self.app.redis_wrapper = self.get_redis_wrapper()
        self.init_config_sync_thread(self.app.redis_wrapper.r.pubsub())

        self.app.ali_pay = self.get_ali_pay_api()
        self.app.wx_pay = self.get_wx_pay_api()
        self.app.secure_tools = self.get_secure_tools()
        self.app.app_conf = self.get_app_config(self.app.redis_wrapper.r)
        self.app.cargo_conf = self.app.app_conf.cargo_conf_inst
        self.app.growth_system = self.get_growth_system()
        self.app.async_im = self.get_async_im()
        self.init_db_conn_pool()


class DatabaseServer(ServerBase):
    def init_app(self):
        self.init_db_conn_pool()
        self.app = CommonApplication(DB_TABLE)
        self.app.db_conn = self.get_db_conn()

    def init_async_http_client(self):
        pass

    def parse_server_conf(self, path):
        import configs.config_wrapper
        self.server_cfg.set_config_component('mysql', configs.config_wrapper.MysqlConfig())
        if not self.server_cfg.parse(path):
            print ("Parse config file [%s] failed." % self.COMMON_CONFIG_FILE)
            exit(1)


class OperationServer(ServerBase):
    def init_app(self):
        from routing_table import OP_TABLE
        self.app = CommonApplication(OP_TABLE, static_path=os.path.join(os.path.dirname(__file__), 'mpages'))
        self.app.db_conn = self.get_db_conn()

# coding: utf-8

import datetime
import logging
import os

import tornado.concurrent
import tornado.httpclient
import tornado.ioloop
import tornado.web

import configs.config_wrapper as Configs
from thirdsupport.live_requests import LiveRequests


class ServerApp(tornado.web.Application):
    def __init__(self, **kwargs):
        super(ServerApp, self).__init__(**kwargs)

    def add_resource(self, name, value):
        if hasattr(self, name):
            raise Exception('Attribute [%s] already exist.' % name)
        setattr(self, name, value)


class ServerBase(object):
    def __init__(self, work_dir, bind_addr, port, config_path):
        self.work_dir = work_dir
        self.app = None
        if bind_addr == '0.0.0.0':
            self.bind_addr = ''
        else:
            self.bind_addr = bind_addr
        self.port = port
        self.db_checked = False

        self.COMMON_CONFIG_FILE = os.path.join(self.work_dir, "server-config/server.cfg")

        self.server_cfg = Configs.ConfigWrapper()
        self.fp_cfg = config_path if config_path else self.COMMON_CONFIG_FILE
        self.parse_server_conf(self.fp_cfg)
        self.init_async_http_client()
        self.config_thread = None
        self.game_sync_thread = None
        self.ioloop = tornado.ioloop.IOLoop.instance()

    def init_async_http_client(self):
        # set max clients for async http client.
        tornado.httpclient.AsyncHTTPClient(max_clients=int(self.server_cfg.common.max_async_client))

    def start_server(self):
        self.init_app()
        self.app.listen(self.port, address=self.bind_addr, xheaders=True)
        logging.info("start server on [{}:{}].".format(self.bind_addr, self.port))
        self._start_threads()
        self.app.srv_start_time = datetime.datetime.now()
        self.ioloop.start()

    def stop_server(self):
        from model.table_base import TableBase
        self._stop_threads()
        if hasattr(TableBase, '_thread_pool'):
            TableBase._thread_pool.shutdown()
        self.ioloop.stop()
        self.app.summary()

    def parse_server_conf(self, path):
        cfg_dir = os.path.split(self.fp_cfg)[0]
        self.server_cfg.set_config_component('mysql', Configs.MysqlConfig())
        self.server_cfg.set_config_component('redis', Configs.RedisConfig())
        self.server_cfg.set_config_component('credits', Configs.UserCreditsConfig())
        self.server_cfg.set_config_component('business', Configs.BusinessConfig(cfg_dir))
        self.server_cfg.set_config_component('qiniu', Configs.QiniuConfig())
        if not self.server_cfg.parse(path):
            print ("Parse config file [%s] failed." % self.COMMON_CONFIG_FILE)
            exit(1)

    def check_db_status(self):
        if not self.db_checked:
            from model.db_wrapper import get_conn
            conn = get_conn(self.server_cfg)
            out = conn.query('show procedure status')
            plist = [itr['Name'] for itr in out if itr['Db'] == self.server_cfg.mysql.database]
            if len(plist) < 3:
                logging.fatal('[NO]Lack procedure. it is abnormal. info:[{}]'.format(plist))
                raise Exception('Check database failed.')
            else:
                for item in ('create_user_by_phone', 'create_active', 'create_topic'):
                    if item not in plist:
                        logging.fatal('[NO]Lack procedure[{}]. it is abnormal. info:[{}]'.format(item, plist))
                        raise Exception('Check database failed.')
                logging.info('[YES]Enough procedure in database. info:[{}]'.format(plist))
            self.db_checked = True

    def init_app(self):
        raise Exception('method init_app has not been implemented.')

    @staticmethod
    def register_cache_worker(cache_wrapper):
        from model.cache import GroundCache
        cache_wrapper.register_cache(GroundCache.cache_name, GroundCache)
        from model.cache import LiveCache
        cache_wrapper.register_cache(LiveCache.cache_name, LiveCache)
        from model.cache.server_cache import ServerCache
        cache_wrapper.register_cache(ServerCache.cache_name, ServerCache)
        from model.cache.user_info_cache import UserInfoCache
        cache_wrapper.register_cache(UserInfoCache.cache_name, UserInfoCache)
        from model.cache import UserResCache
        cache_wrapper.register_cache(UserResCache.cache_name, UserResCache)

    def init_config_sync_thread(self, pubsub):
        if not self.config_thread:
            from utils.subscriber import SubscriberThread
            self.config_thread = SubscriberThread(pubsub, self.server_cfg.redis.config_channel)

    def init_celery_client(self):
        '''
        **Important**: when deploy, make sure you set broker in celery_service.celery
        '''
        from celeryapp.funboxapp import init_celery_app
        logging.info('init celery app with broker:{}'.format(self.server_cfg.celery.broker))
        init_celery_app(self.server_cfg.celery.broker)
        from celeryapp.tasks import app_status_check
        # check if celery is fine
        app_status_check.delay('Server@{}:{}'.format(self.bind_addr, self.port))
        # import tcelery
        # tcelery.setup_nonblocking_producer(celery_app=app)
        # tcelery is too old for celery 4.0.2

    def init_db_conn_pool(self):
        from model.table_base import TableBase
        from concurrent.futures import ThreadPoolExecutor
        setattr(TableBase, '_io_loop', self.ioloop)
        setattr(TableBase, '_thread_pool', ThreadPoolExecutor(self.server_cfg.mysql.pool_size))
        from model.db_wrapper import get_conn_pool
        get_conn_pool(self.server_cfg)
        self.check_db_status()

    def init_game_sync_thread(self, pubsub):
        if not self.game_sync_thread:
            from utils import subscriber
            import model.messgemodel
            self.game_sync_thread = subscriber.SubscriberThread(pubsub, model.messgemodel.CHANNEL_GAME_MSG)

    def get_host_ctrl(self, redis_wrapper):
        from controller.hostctrl import HostController
        from model.cache import LiveCache
        host_ctrl = HostController(redis_wrapper.get_cache(LiveCache.cache_name))
        if not self.game_sync_thread:
            raise ValueError('ServerBase.game_sync_thread not set.')
        self.game_sync_thread.ez_add_handler(host_ctrl.on_game_notification)
        self.game_sync_thread.ez_add_handler(host_ctrl.on_game_over)
        return host_ctrl

    def get_watcher_ctrl(self):
        from controller.watcherctrl import WatcherController
        wc = WatcherController()
        if not self.game_sync_thread:
            raise ValueError('ServerBase.game_sync_thread not set.')
        self.game_sync_thread.ez_add_handler(wc.on_game_notification)
        self.game_sync_thread.ez_add_handler(wc.on_room_closed)
        self.game_sync_thread.ez_add_handler(wc.on_game_closed)
        self.game_sync_thread.ez_add_handler(wc.on_game_started)
        self.game_sync_thread.ez_add_handler(wc.on_start_live)
        return wc

    def get_game_rpc(self):
        from utils.rpcfrmwrk import RpcClient
        return RpcClient('{}/exp/rpc/game'.format(self.server_cfg.living.game.rpc_host))

    def get_async_im(self):
        from thirdsupport.yunxin import YunXinAPI
        return YunXinAPI(self.server_cfg.yx.app_key, self.server_cfg.yx.app_secret,
                         self.server_cfg.yx.host, self.server_cfg.yx.super_user)

    def get_async_live(self):
        return LiveRequests(
            self.server_cfg.yx.video.app_key, self.server_cfg.yx.video.secret, self.server_cfg.yx.video.host)

    def get_redis_wrapper(self):
        from model.cache import CacheWrapper
        redis_wrapper = CacheWrapper(self.server_cfg)
        logging.info('[YES] Redis server ok, info:[{}]'.format(redis_wrapper.redis_info()))
        self.register_cache_worker(redis_wrapper)
        return redis_wrapper

    def get_daily_task(self, redis_wrapper):
        from controller.daily_task_manager import DailyTaskManager
        return DailyTaskManager(redis_wrapper, self.server_cfg.credits)

    def get_secure_tools(self):
        from utils.util_tools import SecureTool
        secret = self.server_cfg.common.pay_secret
        return SecureTool(secret)

    def get_qiniu_api(self):
        from thirdsupport.qiniu_api import QiniuApi
        import datetime
        qa = QiniuApi(
            self.server_cfg.qiniu.app_key, self.server_cfg.qiniu.app_secret,
            self.server_cfg.qiniu.buckets, self.server_cfg.qiniu.timeout
        )
        bucket = self.server_cfg.qiniu.buckets[0][0]
        fpath = '/tmp/servercheck.txt'
        qiniu_key = datetime.datetime.today().strftime('test_%Y%m%d%H%M%S.txt')
        with open(fpath, 'w') as f:
            f.write(datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
        if not qa.upload_file(fpath, bucket, qiniu_key):
            raise RuntimeError('check qiniu conf failed.')
        return qa

    def get_ali_pay_api(self):
        from pay.zhifubao import AliPayApi
        pay_cfg = self.server_cfg.pay
        return AliPayApi(
            pay_cfg.alipay.app_id, pay_cfg.server.host + '/pay/cb/zfb',
            self._conf_abs_path(pay_cfg.alipay.prv_key_file), self._conf_abs_path(pay_cfg.alipay.pub_key_file),
            pay_cfg.alipay.api_gate)

    def get_wx_pay_api(self):
        from pay.weixin import WeiXinApi
        pay_cfg = self.server_cfg.pay
        return WeiXinApi(
            pay_cfg.weixin.app_id, pay_cfg.weixin.secret, pay_cfg.weixin.mch_id,
            pay_cfg.weixin.api_addr, pay_cfg.server.host + '/pay/cb/wx')

    def get_tecent_access_tool(self):
        from thirdsupport.weixin_login import WeiXinLoginTool
        return WeiXinLoginTool(
            self.server_cfg.access.weixin.app_id,
            self.server_cfg.access.weixin.app_secret,
            self.server_cfg.access.weixin.api_domain
        )

    def get_app_config(self, r):
        from configs.versionconfig import AppConfig
        from model.cache.cache_define import RedisStr
        key = RedisStr.AppConfigHKey
        ac = AppConfig()
        app_conf = self.server_cfg.app
        self._update_from_file(
            self._conf_abs_path(app_conf.cargo_cfg_file), ac.cargo_routing_key, ac.reset_cargo,
            r, key, RedisStr.AppCargoConfField
        )
        self._update_from_file(
            self._conf_abs_path(app_conf.ver_cfg_file), ac.version_routing_key, ac.reset_version,
            r, key, RedisStr.AppVersionConfField
        )
        self._update_from_file(
            self._conf_abs_path(app_conf.banner_cfg_file), ac.banner_routing_key, ac.reset_banner,
            r, key, RedisStr.AppBannerConfField
        )
        return ac

    def get_game_config(self):
        from configs.live_res_config import GameConfig
        return GameConfig(self._conf_abs_path(self.server_cfg.living.game.cfg_file))

    def get_gift_config(self):
        from configs.live_res_config import GiftConfig
        return GiftConfig(self._conf_abs_path(self.server_cfg.living.gift.cfg_file))

    def get_db_conn(self):
        from model.db_wrapper import get_conn
        self.check_db_status()
        return get_conn(self.server_cfg)

    @staticmethod
    def get_user_center(redis_conn, async_im):
        from controller.usercenter import UserCenter
        return UserCenter(redis_conn, async_im)

    @staticmethod
    def get_ground_center(redis_wrapper):
        from controller.groundcenter import GroundCenter
        from model.cache import GroundCache
        return GroundCenter(redis_wrapper.get_cache(GroundCache.cache_name))

    @staticmethod
    def get_active_cache():
        from utils.repoze.lru import ExpiringLRUCache
        return ExpiringLRUCache(512, 10)

    @staticmethod
    def get_user_detail_cache():
        from utils.repoze.lru import ExpiringLRUCache
        return ExpiringLRUCache(4096, 1)

    def get_live_biz(self, redis_wrapper, qiniu_api, gift_conf):
        from controller.live_operator import LiveManager
        lm = LiveManager(redis_wrapper, qiniu_api, gift_conf)
        return lm

    @staticmethod
    def get_game_manager(game_conf, redis_wrapper):
        import games.gamemodule
        from utils.rpcfrmwrk import RpcHandler
        gm = games.gamemodule.GameManager(game_conf, redis_wrapper)
        gm.do_job()
        RpcHandler.inject_rpc(gm.rpc_add_bet)
        RpcHandler.inject_rpc(gm.rpc_get_game_snapshot)
        RpcHandler.inject_rpc(gm.rpc_start_game)
        return gm

    def get_growth_system(self):
        from controller.growth_system import GrowthSystem
        return GrowthSystem(self.app)

    def _conf_abs_path(self, fname):
        cfg_dir = os.path.split(self.fp_cfg)[0]
        return os.path.join(cfg_dir, fname)

    def _update_from_file(self, conf_file, routine_key, reset_func, redis_inst, redis_key, redis_field):
        import json
        val = redis_inst.hget(redis_key, redis_field)
        if not val:
            # update config from file, then set to redis.
            with open(conf_file) as f:
                s_cfg = f.read()
            data = json.loads(s_cfg)
            reset_func(data)
            logging.info('update config from %s to redis.', conf_file)
            redis_inst.hset(redis_key, redis_field, s_cfg)
        else:
            # update config from redis
            logging.info('get config from redis:%s %s.', redis_key, redis_field)
            data = json.loads(val)
            reset_func(data)
        if not self.config_thread:
            raise ValueError('config_thread not set.')
        self.config_thread.add_handler(routine_key, reset_func)

    def _start_threads(self):
        if self.config_thread:
            self.config_thread.start()
        if self.game_sync_thread:
            self.game_sync_thread.start()

    def _stop_threads(self):
        if self.config_thread:
            self.config_thread.join()
        if self.game_sync_thread:
            self.game_sync_thread.join()

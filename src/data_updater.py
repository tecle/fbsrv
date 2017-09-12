# coding: utf-8

'''
This script is used for updating live watch number,
maybe we will use it for check live status.
because there may be a lot of server, it is bad to put check logic in server.
'''

import os
import signal
import sys

ROOT = os.getcwd()
sys.path.append(os.path.join(ROOT, 'libs'))
sys.path.append(os.path.join(ROOT, 'src'))

import redis
import logging
import tornado.ioloop
import configs.config_wrapper as Configs
from functools import partial
from model.cache.cache_define import RedisStr
from thirdsupport.yunxin import YunXinAPI
from tornado.options import options, define

ChannelLiveStats = 1


class DataUpdater(object):
    def __init__(self, conf_path=None):
        if not conf_path:
            raise ValueError('conf_path is None.')
        self.cfg = Configs.ConfigWrapper()
        self.cfg.set_config_component('redis', Configs.RedisConfig())
        if not self.cfg.parse(os.path.join(conf_path)):
            print ("Parse config file [%s] failed." % conf_path)
            exit(1)
        self.r = redis.Redis(
            host=self.cfg.redis.host,
            port=self.cfg.redis.port,
            db=self.cfg.redis.db,
            password=self.cfg.redis.pwd,
            max_connections=2
        )
        logging.info(self.r.info())
        self.yunxin = YunXinAPI(
            self.cfg.yx.app_key, self.cfg.yx.app_secret, self.cfg.yx.host, self.cfg.yx.super_user)
        self.timer = None
        self.wake_interval = 1
        self.counter = 0
        self.shutdown = False
        self.update_magic_num = 0b1111  # update every 16 seconds

    def update_live_viewer_number(self):
        live_list = self.r.smembers(RedisStr.LivingListSKey)
        if live_list:
            live_list = [i for i in live_list]
            logging.info('update live data:[{}]'.format(live_list))
            p = self.r.pipeline()
            for live_id in live_list:
                p.hget(RedisStr.LiveHKeyPtn % live_id, RedisStr.LiveChatRoomField)
            room_list = p.execute()
            view_data = {}
            for i, room_id in enumerate(room_list):
                logging.info('get room[{}] online number.'.format(room_id))
                if room_id:
                    self.yunxin.get_chat_room_info(
                        room_id,
                        callback=partial(self.on_finish_get_room_info, live_list[i], view_data, len(live_list)))
                else:
                    view_data[live_list[i]] = 0
        self.do_stop()

    def on_finish_get_room_info(self, live_id, view_data, sentinel, response):
        if not response:
            view_data[live_id] = None
            logging.warning('get room number for live [{}] failed.'.format(live_id))
        else:
            view_data[live_id] = response['chatroom']['onlineusercount']
        if len(view_data) >= sentinel:
            p = self.r.pipeline()
            for live_id, view_num in view_data.items():
                p.hset(RedisStr.LiveHKeyPtn % live_id, RedisStr.LiveCurrentViewNumField, view_num)
            p.execute()
            logging.info('update live view number over:[{}]'.format(view_data))
            self.do_stop()

    def do_check(self):
        self.counter += 1
        reset = 0
        if self.counter & self.update_magic_num == self.update_magic_num:
            # update every 7 seconds.
            self.update_live_viewer_number()
            reset = 1
        if reset == 2:
            logging.debug('reset counter:[{}]->[0]'.format(self.counter))
            self.counter = 0  # avoid number too large.

    def stop(self, *args):
        logging.info('args[{}], prepare to stop.'.format(args))
        self.shutdown = True

    def run(self):
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGQUIT, self.stop)

        loop = tornado.ioloop.IOLoop.instance()
        self.timer = tornado.ioloop.PeriodicCallback(self.do_check, self.wake_interval * 1000, loop)
        self.timer.start()
        loop.start()

    def do_stop(self):
        if self.shutdown:
            tornado.ioloop.IOLoop.instance().stop()


if __name__ == "__main__":
    define("config", '', help="config file", type=str)
    default_params = {
        '--log-to-stderr': 'false',
        '--log_file_prefix': os.path.join(ROOT, 'logs/du.log'),
        '--log_rotate_mode': 'time',
        '--logging': 'info'
    }
    sys.argv += ['%s=%s' % (k, v) for k, v in default_params.items()]
    options.parse_command_line()

    du = DataUpdater(options.config)
    du.run()

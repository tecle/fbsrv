# coding: utf-8

from __future__ import absolute_import, print_function, with_statement  # , unicode_literals

import sys

reload(sys)
sys.setdefaultencoding('utf-8')

from concurrent.futures import ThreadPoolExecutor
from .dingtalkrobot import DingTalkRobot
from .kvcfgparser import KeyValueConfigParser
from .getuiapi import GeTuiAPI
import Queue

'''
start cmd:python -m celeryapp.funboxapp {config_file_path}
'''

import torndb
import logging
from celery import Celery

app = Celery('funboxapp')
POOL_SIZE = 4


class AppResource(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst_'):
            cls._inst_ = super(AppResource, cls).__new__(cls, *args)
            cls._inst_.init_resource()
        return cls._inst_

    def init_resource(self):
        '''init database connection and thread pool'''
        from .appconfig import funbox_conf_file
        self.conf = KeyValueConfigParser()
        self.conf.parse(funbox_conf_file)
        self._idle_conn = Queue.Queue()
        self._init_db_pool()
        self._tpool = ThreadPoolExecutor(POOL_SIZE)
        self._opinion_robot = DingTalkRobot(self.conf.robot.url, self.conf.robot.opinion.token)
        self._support_robot = DingTalkRobot(self.conf.robot.url, self.conf.robot.support.token)
        self._getui = GeTuiAPI(
            self.conf.getui.host, self.conf.getui.app_id, self.conf.getui.app_key,
            self.conf.getui.app_secret, self.conf.getui.master_secret
        )

    @property
    def thread_pool(self):
        return self._tpool

    @property
    def conn(self):
        return self._connection

    def query(self, query, *args, **kwargs):
        return self._safe_insert(query, *args, **kwargs)

    def push_data(self, client_id, data):
        return self._tpool.submit(self._getui.push_to_one, client_id, data)

    def insert_to_database(self, query, *args, **kwargs):
        return self._tpool.submit(self._safe_insert, query, *args, **kwargs)

    def alert_opinion(self, msg):
        return self._tpool.submit(self._opinion_robot.send_text_msg, msg)

    def alert_need_support(self, msg):
        return self._tpool.submit(self._support_robot.send_text_msg, msg)

    def _safe_insert(self, q, *args, **kwargs):
        res = conn = None
        try:
            conn = self._idle_conn.get()
            res = conn.insert(q, *args, **kwargs)
        except:
            logging.exception('insert failed.\n query: %s', q % tuple(args))
        finally:
            if conn:
                self._idle_conn.put(conn)
            return res

    def _init_db_pool(self):
        host = "{}:{}".format(self.conf.db.host, int(self.conf.db.get('port', 3306)))
        database = self.conf.db.name
        user = self.conf.db.user
        password = self.conf.db.password
        for _ in range(POOL_SIZE):
            self._idle_conn.put(torndb.Connection(host, database, user, password, time_zone="+8:00"))

    def _destroy(self):
        if self._connection:
            self._connection.close()
            self._connection = None
        if self._tpool:
            self._tpool.shutdown()

    def __del__(self):
        self._destroy()


def init_celery_app(broker):
    app.conf.update(broker_url=broker)


def get_celery_conf_from_file(file_path):
    cfg_wanted = (
        'celery.concurrency',
        'celery.broker',
        'celery.loglevel',
        'celery.logfile',
        'db.host',
        'db.port',
        'db.name',
        'db.user',
        'db.password',
        'robot.opinion.token',
        'robot.support.token',
        'robot.url'
    )
    with open(file_path) as f:
        out = {
            cfg_key: line[line.find('=') + 1:].strip()
            for line in f for cfg_key in cfg_wanted if line.startswith(cfg_key)
            }
    return out


def run():
    import os
    import sys

    cfg_file_path = sys.argv.pop(1)
    abs_path = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(abs_path, 'appconfig.py'), 'w') as f:
        f.write('funbox_conf_file = "{}"\n'.format(cfg_file_path))

    from .appconfig import funbox_conf_file
    log_file = '/var/log/celery/celery.log'
    conf = KeyValueConfigParser()
    if not conf.parse(funbox_conf_file):
        raise RuntimeError('get config from %s failed.' % funbox_conf_file)

    extra_conf = [
        'worker',
        '-f', conf.celery.get('logfile', log_file),
        '-I', 'celeryapp.tasks',
        '-b', conf.celery.broker,
        '-A', 'celeryapp.funboxapp',
        '-l', conf.celery.get('loglevel', 'INFO'),
        '-c', conf.celery.get('concurrency', '2')
    ]
    app.start(sys.argv + extra_conf)


if __name__ == "__main__":
    run()

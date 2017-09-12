# coding: utf-8
import os
import logging


class ConfigObject(object):
    def __repr__(self):
        out = []
        for attr in dir(self):
            if not attr.startswith('__'):
                attr_val = getattr(self, attr)
                if isinstance(attr_val, ConfigObject):
                    out += ['{}.{}'.format(attr, line) for line in repr(attr_val).split('\n')]
                else:
                    out.append('{}={}'.format(attr, attr_val))
        return '\n'.join(out)


class QiniuConfig(object):
    def __init__(self):
        self.app_key = None
        self.app_secret = None
        self.buckets = []
        self.timeout = None

    def parse(self, kv_map):
        logging.info('begin parse qiniu config')
        self.app_key = kv_map['qiniu.app.key']
        self.app_secret = kv_map['qiniu.app.secret']
        for i in range(1, 50):
            key1, key2 = 'qiniu.bucket.name.%d' % i, 'qiniu.bucket.url.%d' % i
            if key1 not in kv_map or key2 not in kv_map:
                continue
            self.buckets.append((kv_map[key1], kv_map[key2]))
        if not self.buckets:
            raise Exception('at least 1 bucket required.')
        self.timeout = int(kv_map['qiniu.pic.timeout'])


class UserCreditsConfig(object):
    def __init__(self):
        self.publish_reward = None
        self.publish_reward_max = None
        self.comment_reward = None
        self.comment_reward_max = None
        self.chat_reward = None
        self.chat_reward_max = None
        self.watch_reward = None
        self.watch_reward_max = None
        self.login_reward = None
        self.login_reward_max = None

    def parse_and_set_value(self, value, attr_name):
        tmp = [int(v) for v in value.split('/')]
        setattr(self, attr_name, tmp[0])
        setattr(self, attr_name + '_max', tmp[1])

    def parse(self, kv_map):
        logging.info('Begin parse user credits config...')
        self.parse_and_set_value(kv_map['credits.publish_reward'], 'publish_reward')
        self.parse_and_set_value(kv_map['credits.comment_reward'], 'comment_reward')
        self.parse_and_set_value(kv_map['credits.chat_reward'], 'chat_reward')
        self.parse_and_set_value(kv_map['credits.watch_reward'], 'watch_reward')
        self.parse_and_set_value(kv_map['credits.login_reward'], 'login_reward')


from configs.credits_config import CreditsConfig
from configs.login_reward_config import LoginRewardConfig
from configs.daily_task_reward_config import DailyTaskRewardConfig


class BusinessConfig(object):
    def __init__(self, conf_file_dir):
        self.login_reward_config = LoginRewardConfig()
        self.credits_config = CreditsConfig()
        self.daily_task_config = DailyTaskRewardConfig()
        self.conf_dir = conf_file_dir

    def parse(self, kv_map):
        logging.info('Begin parse business config...')
        reward_config_path = os.path.join(self.conf_dir, kv_map['business.login_config_file'])
        if not self.credits_config.parse_from_json_file(reward_config_path) \
                or not self.login_reward_config.parse_from_json_file(reward_config_path):
            raise Exception('Parse json config failed.')
        daily_config_path = os.path.join(self.conf_dir, kv_map['business.daily_task_config_file'])
        self.daily_task_config.parse_from_json_file(daily_config_path)


class CommonConfig(object):
    def __init__(self):
        self.db_layer_host = None
        self.server_mode = None
        self.max_async_clients = None
        self.pay_secret = None

    def parse(self, kv_map):
        logging.info('Begin parse common config...')
        self.db_layer_host = kv_map['common.db_layer.host']
        self.server_mode = kv_map['common.server.mode']
        if self.server_mode not in ['debug', 'db']:
            raise Exception('Invalid server mode. Expect:debug|db')
        self.max_async_clients = int(kv_map['common.max_async_client'])
        self.pay_secret = kv_map.get('common.pay_secret', None)


class MysqlConfig(object):
    def __init__(self):
        self.host = None
        self.database = None
        self.user = None
        self.pwd = None
        self.pool_size = None

    def parse(self, kv_map):
        logging.info('Begin parse mysql config...')
        self.host = "%s:%s" % (kv_map.get("db.host", "127.0.0.1"), kv_map.get("db.port", "3306"))
        self.database = kv_map["db.name"]
        self.user = kv_map["db.user"]
        self.pwd = kv_map["db.password"]
        self.pool_size = int(kv_map.get('db.poolsize', 4))


class RedisConfig(object):
    def __init__(self):
        self.host = None
        self.port = None
        self.pwd = None
        self.heartbeat_exp_time = None
        self.db = None
        self.config_channel = None
        self.srv_cfg_key = None

    def parse(self, kv_map):
        logging.info('Begin parse redis config...')
        self.host = kv_map.get("redis.host", "127.0.0.1")
        self.port = int(kv_map.get("redis.port", 6379))
        self.pwd = kv_map.get('redis.pwd', None)
        if not self.pwd:
            self.pwd = None
        self.heartbeat_exp_time = kv_map.get('redis.heartbeat.expire_time', 360)
        self.db = kv_map.get('redis.db', 0)
        self.config_channel = kv_map['redis.cfg_channel']
        self.srv_cfg_key = kv_map['redis.cfg_key']


class ConfigWrapper(object):
    def __new__(cls):
        if not hasattr(cls, '_inst'):
            cls._inst = super(ConfigWrapper, cls).__new__(cls)
            cls._inst.initialize()
        return cls._inst

    def initialize(self):
        self.components = []

    def parse(self, cfg_file_path):
        with open(cfg_file_path, "rb") as f:
            cfg_ctnt = f.read()
        if not cfg_ctnt:
            logging.error("Read file failed.")
            return False
        kv_map = {}
        for line in cfg_ctnt.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pos = line.find("=")
            if pos < 0:
                continue
            key = line[0:pos].strip()
            val = self._process_val(line[pos + 1:])
            kv_map[key] = val
            self.set_conf(key, val)
        return self._extract_info(kv_map)

    def set_config_component(self, name, inst):
        setattr(self, name, inst)
        self.components.append(inst)

    def _extract_info(self, kv_map):
        try:
            for cfg_component in self.components:
                cfg_component.parse(kv_map)
        except Exception, e:
            logging.exception("Get param error.")
            return False
        return True

    def set_conf(self, key, val):
        logging.debug('Set conf: %48s -> %s', key, val)
        sections = key.split('.')
        inst = self
        for sec_name in sections[:-1]:
            if not hasattr(inst, sec_name):
                setattr(inst, sec_name, ConfigObject())
            inst = getattr(inst, sec_name)
        setattr(inst, sections[-1], val)

    def _process_val(self, value):
        stack = []
        ret = []
        for ch in value.strip():
            if stack and stack[-1] == '\\':
                ret.append(ch)
                stack.pop(-1)
            elif ch == '\\':
                stack.append(ch)
            elif ch == '"':
                if stack and stack[-1] == '"':
                    return ''.join(ret)
                if not stack:
                    if ret:
                        raise ValueError('invalid value: %s' % value.strip())
                    stack.append('"')
            elif ch == '#':
                if stack and stack[-1] == '"':
                    ret.append(ch)
                else:
                    return ''.join(ret).strip()
            else:
                ret.append(ch)
        return ''.join(ret).strip()

    def __repr__(self):
        out = []
        for attr in dir(self):
            if not attr.startswith('__'):
                attr_val = getattr(self, attr)
                if isinstance(attr_val, ConfigObject):
                    out += ['{}.{}'.format(attr, line) for line in repr(attr_val).split('\n')]
        return '\n'.join(out)

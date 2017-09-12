# coding: utf-8
from __future__ import absolute_import

import httplib
import json
import time
import traceback
import urllib2
from functools import wraps

import redis
import torndb
from qiniu import Auth, put_file, etag

from thirdsupport.yunxin import YunXinAPI

help_info = {}


class HelperConf(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst'):
            cls._inst = super(HelperConf, cls).__new__(cls)
            cls._inst.initialize()
        return cls._inst

    def initialize(self):
        self.conf_file = None
        self.server_gate = 'https://chat.leeqo.cn'


def cach_return(func):
    cache_data = {}

    @wraps(func)
    def func_wrapper():
        if func.__name__ in cache_data:
            return cache_data[func.__name__]
        r = func()
        cache_data[func.__name__] = r
        return r

    return func_wrapper


def gen_prompt(comment, func_type):
    def wrapper(func):
        def doit():
            print '-' * 70
            func()
            want_more = raw_input('继续? y/n:')
            if want_more.upper() != 'Y':
                exit(0)
        debug_info = help_info.setdefault(func_type, [])
        debug_info.append((comment, doit))
        return doit

    return wrapper


def show_notice():
    print '*' * 70
    keys = help_info.keys()
    func_list = ['{}, {}'.format(i, s) for i, s in enumerate(keys)]
    choose = int(raw_input('\n{}\n请输入选择的功能:'.format('\n'.join(func_list))))
    funcs = None
    if choose < 0 or choose >= len(keys):
        print '错误的选项.'
    else:
        funcs = help_info[keys[choose]]
        for i, item in enumerate(funcs):
            print '{0}. {1}'.format(i, item[0])
    return funcs


@cach_return
def get_qiniu_api():
    from thirdsupport.qiniu_api import QiniuApi
    from configs.config_wrapper import QiniuConfig, ConfigWrapper
    wrapper = ConfigWrapper()
    wrapper.set_config_component('qiniu', QiniuConfig())
    wrapper.parse(HelperConf().conf_file)
    return QiniuApi(wrapper.qiniu.app_key, wrapper.qiniu.app_secret, wrapper.qiniu.buckets, 300)


@cach_return
def get_db_conn():
    from configs.config_wrapper import MysqlConfig, ConfigWrapper
    x = ConfigWrapper()
    x.set_config_component('mysql', MysqlConfig())
    x.parse(HelperConf().conf_file)
    print 'db:', x.mysql.host, x.mysql.database, x.mysql.user, x.mysql.pwd
    return torndb.Connection(x.mysql.host, x.mysql.database, x.mysql.user, x.mysql.pwd)


@cach_return
def get_redis_inst():
    from configs.config_wrapper import ConfigWrapper, RedisConfig
    x = ConfigWrapper()
    x.set_config_component('r', RedisConfig())
    x.parse(HelperConf().conf_file)
    print 'redis:', x.r.host, x.r.port, x.r.pwd, x.r.db
    return redis.Redis(host=x.r.host, port=x.r.port, password=x.r.pwd, db=x.r.db)


@cach_return
def get_config_channel():
    from configs.config_wrapper import ConfigWrapper, RedisConfig
    x = ConfigWrapper()
    x.set_config_component('r', RedisConfig())
    x.parse(HelperConf().conf_file)
    return x.r.config_channel


@cach_return
def get_config_key():
    from configs.config_wrapper import ConfigWrapper, RedisConfig
    x = ConfigWrapper()
    x.set_config_component('r', RedisConfig())
    x.parse(HelperConf().conf_file)
    return x.r.src_cfg_key


@cach_return
def get_async_im():
    from configs.config_wrapper import ConfigWrapper
    x = ConfigWrapper()
    x.parse(HelperConf().conf_file)
    return YunXinAPI(x.yx.app_key, x.yx.app_secret, x.yx.host, x.yx.super_user)


class QiniuUploader(object):
    def __init__(self, enable_debug=False, env='test'):
        self.debug = enable_debug
        # 需要填写你的 Access Key 和 Secret Key
        if env == 'test':
            self.access_key = 'Q3K6diT8i9fJfVAI4fWHQvW1mlmqZKK1gG-FI4em'
            self.secret_key = 'stSK3tA2QIt3dAEDlTxs5G-Vl72hxf2Rh8EP8S4N'
        else:
            self.access_key = 'w_x0Zgc6T23ZEepH3Kmf0pzXi7pDVMeltepjgIhb'
            self.secret_key = 'ZdtlR31KL7LS9k3KkevI2dRp0R1oO6fV_3BbgkEZ'
        # 构建鉴权对象
        self.q = Auth(self.access_key, self.secret_key)
        # 要上传的空间
        self.bucket_name = 'testbucket'

    def upload_file(self, f, key):
        print 'upload file:[%s]->[%s]' % (f, key)
        # 生成上传 Token，可以指定过期时间等
        token = self.q.upload_token(self.bucket_name, key, 3600)
        out = "{}:{}".format(self.bucket_name, key)
        if self.debug:
            print "debug:upload:[{}],[{}],[{}]".format(token, key, f)
        else:
            # 要上传文件的本地路径
            ret, info = put_file(token, key, f)
            print('upload result:[{}],[{}]'.format(ret, info))
            if ret['key'] != key or ret['hash'] != etag(f):
                print 'upload failed.'
        return out

    def do_upload(self, uid, ori_file_path):
        ori_file = os.path.basename(ori_file_path)
        key = '%s_%d%s' % (uid, int(time.time() * 1000), os.path.splitext(ori_file)[1])
        return self.upload_file(ori_file_path, key)

    @staticmethod
    def gen_fname(uid, ori_file):
        suffix = ori_file[ori_file.rfind("."):]
        return '%s_%d%s' % (uid, int(time.time() * 1000), suffix)


def http_request(url, data):
    time.sleep(0.01)
    try:
        req = urllib2.Request(url, data=json.dumps(data, ensure_ascii=False), headers={'debug': 'whoisyourdaddy'})
        rsp = urllib2.urlopen(req)
        body = rsp.read()
        print body
        obj = json.loads(body)
        if obj['status'] != 'OK':
            print "info:{}".format(obj['code'])
            raise Exception('bad status')
        return obj
    except Exception:
        print "post data {} failed.".format(data)
        traceback.print_exc()
        return None


def register_user(nick, sex, sign, born, idx):
    rsp = http_request('{}/login/register'.format(HelperConf().server_gate), {
        "phone": "200{:08d}".format(idx),
        "country": "86",
        "pwd": "e10adc3949ba59abbe56e057f20f883e"
    })
    if rsp:
        uid = rsp['code']
        rsp = http_request('{}/login/update'.format(HelperConf().server_gate), {
            "uid": uid,
            "nick": nick,
            "sign": sign,
            "born": born,
            "gender": sex
        })
        if not rsp:
            print "add user failed."


def send_http_request(url, params):
    conn = httplib.HTTPConnection(HelperConf().server_gate)
    conn.request('POST', url, body=json.dumps(params), headers={
        "Content-type": "application/x-www-form-urlencoded",
        "debug": "whoisyourdaddy"
    })
    resp = conn.getresponse()
    print '请求结果状态码:{0}'.format(resp.status)
    data = resp.read()
    conn.close()
    print '请求返回:[{0}]'.format(data)


def test_redis():
    inf = get_redis_inst().info()
    print 'Redis信息:'
    print '版本:{}'.format(inf['redis_version'])
    print '连接的Slave个数:{}'.format(inf['connected_slaves'])
    print '当前占用内存:{}'.format(inf['used_memory_human'])

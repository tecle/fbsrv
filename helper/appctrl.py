# coding: utf-8

from __future__ import absolute_import

import json

from configs.versionconfig import AppConfig
from model.cache.cache_define import RedisStr
from utils.subscriber import make_pub_message
from .hplcore import gen_prompt, get_redis_inst

import_info = "APP操作集合"
PUB_SUB_CHANNEL = 'CONFIG_CHANNEL'


@gen_prompt('更新版本信息', 'App')
def add_user_to_live_list():
    cur_ver = int(raw_input('当前版本代码:'))
    cur_ver_name = raw_input('当前版本字符串:')
    cur_ver_info = raw_input('当前版本说明:')
    min_ver_need = int(raw_input('最低版本需求:'))
    dl_location = raw_input('APP下载地址:')
    r = get_redis_inst()
    data = {
        "code": cur_ver,
        "text": cur_ver_name,
        "min": min_ver_need,
        "dl": dl_location,
        "info": cur_ver_info
    }
    r.hset(RedisStr.AppConfigHKey, RedisStr.AppVersionConfField, json.dumps(data))
    ac = AppConfig()

    print r.publish(PUB_SUB_CHANNEL, json.dumps(make_pub_message(ac.version_routing_key, data)))


@gen_prompt('更新Banner', 'App')
def add_user_to_live_list():
    count = int(raw_input('Banner个数:'))
    if count <= 0 or count >= 10:
        print "Banner数量错误(太多或者太少)"
        return
    banners = []
    for _ in range(count):
        banner_type = int(raw_input('Banner 类型代码:'))
        banner_data = raw_input('Banner 数据:')
        banners.append({'type': banner_type, 'data': banner_data})
    r = get_redis_inst()
    print r.hset(RedisStr.AppConfigHKey, RedisStr.AppBannerConfField, json.dumps(banners))
    ac = AppConfig()
    print r.publish(PUB_SUB_CHANNEL, json.dumps(make_pub_message(ac.banner_routing_key, banners)))


@gen_prompt('更新商品信息', 'App')
def add_user_to_live_list():
    fp = raw_input('商品配置文件:')
    with open(fp) as f:
        ctnt = f.read()
    obj = json.loads(ctnt)
    r = get_redis_inst()
    print r.hset(RedisStr.AppConfigHKey, RedisStr.AppCargoConfField, ctnt)
    ac = AppConfig()
    print r.publish(PUB_SUB_CHANNEL, json.dumps(make_pub_message(ac.cargo_routing_key, obj)))

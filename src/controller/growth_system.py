# coding: utf-8

import logging
import math
from functools import partial

from model.cache.user_info_cache import UserInfoCache


class VipLevelSystem(object):
    def __init__(self, app):
        self.app = app
        # self.parse_conf(self.app.server_conf.growth.vip_level_conf_file)
        self.user_cache = self.app.redis_wrapper.get_cache(UserInfoCache.cache_name)
        self.conf = [0, 0, 6]
        pre = 6
        for i in xrange(3, 101):
            pre = math.ceil(pre * 1.1)
            self.conf.append(pre + self.conf[i - 1])

    def parse_conf(self, path):
        pass

    def increment_exp(self, uid, amount):
        '''
        :param amount: 单位为分
        '''
        amount /= 100.0
        nick, level, charge_sum = self.user_cache.get_user_vip_level_info(uid)
        next_level_required = self.conf[level]
        charge_sum += amount
        if charge_sum >= next_level_required:
            level += 1
            self.do_level_up(uid, nick, level)
        self.user_cache.update_user_vip_level_info(uid, level, charge_sum)

    def do_level_up(self, uid, nick_name, new_level):
        # 1.broadcast msg to user
        # 2.update to user yunxin card
        self.app.async_im.update_user_card(
            uid, level=new_level, nick_name=nick_name, callback=partial(self.on_finish_update_im_info, uid, new_level))

    @staticmethod
    def on_finish_update_im_info(uid, level, resp):
        if not resp:
            logging.warning('update user[%s] new level[%s] to IM failed.' % (uid, level))


class GrowthSystem(object):
    def __init__(self, app):
        self.app = app
        self.vip_system = VipLevelSystem(app)

    def recharge(self, uid, amount):
        '''
        :param uid: 用户ID
        :param amount: 充值金额, 单位为分
        '''
        self.vip_system.increment_exp(uid, amount)

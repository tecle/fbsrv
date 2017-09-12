# coding: utf-8

import logging

from cache_define import RedisStr
from cache_wrapper import ExtendedCache


# from redis.exceptions import *


class UserResCache(ExtendedCache):
    cache_name = 'ures'

    def __init__(self, redis):
        super(UserResCache, self).__init__(redis_inst=redis)

    def increment_user_credits(self, user_id, increment_val):
        '''credit'''
        return self.r.hincrby(RedisStr.UserHKeyPtn % user_id, RedisStr.UserCreditField, increment_val)

    def increment_user_charm(self, user_id, increment_val):
        return self.r.zincrby(RedisStr.UserCharmZKey, user_id, increment_val)

    def increment_user_money(self, user_id, money):
        '''
        :param user_id: user id
        :param money: integer
        :return:current gold
        '''
        ret = self.r.zincrby(RedisStr.UserTotalFortuneZKey, user_id, money)
        return ret

    def send_gift_to_living_girl(self, uid, lid, cost):
        p = self.r.pipeline()
        p.zincrby(RedisStr.UserTotalFortuneZKey, uid, -cost)
        p.hincrby(RedisStr.LiveHKeyPtn % lid, RedisStr.LiveFortuneEarnedField, cost)
        p.zincrby(RedisStr.UserCharmZKey, lid, cost)
        p.zincrby(RedisStr.DailyRankingZKeyPtn % lid, uid, cost)
        p.zincrby(RedisStr.TotalRankingZKeyPtn % lid, uid, cost)
        ret = p.execute()
        sender_remain, receiver_charm = ret[0], ret[2]
        if sender_remain < 0:
            logging.info('user[%s] send [%d] gold to user[%s] failed.' % (uid, cost, lid))
            p = self.r.pipeline()
            p.zincrby(RedisStr.UserTotalFortuneZKey, uid, cost)
            p.hincrby(RedisStr.LiveHKeyPtn % lid, RedisStr.LiveFortuneEarnedField, -cost)
            p.zincrby(RedisStr.UserCharmZKey, lid, -cost)
            p.zincrby(RedisStr.DailyRankingZKeyPtn % lid, uid, -cost)
            p.zincrby(RedisStr.TotalRankingZKeyPtn % lid, uid, -cost)
            p.execute()
            return False, None
        logging.info('user[%s] send [%d] gold to living girl[%s]' % (uid, cost, lid))
        return True, (sender_remain, receiver_charm)

    def transfer_gold(self, uid, target, cost):
        '''
        :param uid: 赠送者ID
        :param target: 接收者ID
        :param cost: 赠送值
        :return: 成功/失败, (赠送者剩余金币值, 接收者当前魅力值)
        '''
        # 注意, 后面增加金币类型时,需要修改对应的script以及self.gold_types
        p = self.r.pipeline()
        p.zincrby(RedisStr.UserTotalFortuneZKey, uid, -cost)
        p.zincrby(RedisStr.UserTotalFortuneZKey, target, cost)
        p.zincrby(RedisStr.UserCharmZKey, target, cost)
        ret = p.execute()

        sender_remain, receiver_charm = ret[0], ret[2]
        if sender_remain < 0:
            logging.info('user[%s] send [%d] gold to user[%s] failed.' % (uid, cost, target))
            p = self.r.pipeline()
            p.zincrby(RedisStr.UserTotalFortuneZKey, uid, cost)
            p.zincrby(RedisStr.UserTotalFortuneZKey, target, -cost)
            p.zincrby(RedisStr.UserCharmZKey, target, -cost)
            p.execute()
            return False, None
        logging.info('user[%s] send [%d] gold to user[%s]' % (uid, cost, target))
        return True, (sender_remain, receiver_charm)

    def consume_gold(self, uid, cost):
        '''
        :return: boolean:success/fail
        '''
        res = self.r.zincrby(RedisStr.UserTotalFortuneZKey, uid, -cost)
        if res < 0:
            logging.warning('user {0} consume gold failed.'.format(uid))
            self.r.zincrby(RedisStr.UserTotalFortuneZKey, uid, cost)
            return False, None
        return True, res

    def increment_gold(self, uid, amount):
        '''
        Increment the gold number in user's account.
        :return current total fortune
        '''
        return self.r.zincrby(RedisStr.UserTotalFortuneZKey, uid, amount)

    def batch_increment_gold(self, sequence):
        '''
        :param sequence: [(uid, incr), ...]
        :return:[new_fortune, new_fortune...]
        '''
        if not sequence:
            return None
        p = self.r.pipeline()
        for user_id, incr in sequence:
            p.zincrby(RedisStr.UserTotalFortuneZKey, user_id, incr)
        return p.execute()

# coding: utf-8

import logging

from cache_wrapper import ExtendedCache

from model.cache.cache_define import RedisStr


class ServerCache(ExtendedCache):
    cache_name = 'server'

    def __init__(self, redis):
        super(ServerCache, self).__init__(redis_inst=redis)

    def get_hobby(self, size):
        return self.r.srandmember(RedisStr.HobbySKey, size)

    def get_all_hobbies(self):
        '''
        :return: {"hobby id": "hobby value", ...}
        '''
        return self.r.smembers(RedisStr.HobbySKey)

    def set_request_id(self, request_id):
        self.r.set(RedisStr.RequestIdKeyPtn % request_id, '1', ex=10)

    def get_cached_req_data(self, request_id, uid=None):
        logging.debug('get token with uid:{}'.format(uid))
        p = self.r.pipeline()
        p.get(RedisStr.RequestIdKeyPtn % request_id)
        if uid:
            p.hget(RedisStr.UserHKeyPtn % uid, RedisStr.UserTokenValueField)
        res = p.execute()
        logging.debug('cached token data:{}'.format(res))
        return res[0] is not None, res[1] if uid else None

    '''Here is sms operation'''

    def get_sms_code(self, user_phone):
        return self.r.hget(RedisStr.SMSHKeyPtn % user_phone, RedisStr.SMSCodeField)

    def sms_already_send(self, key):
        return self.r.hget(RedisStr.SMSHKeyPtn % key, RedisStr.SMSStatusField) == '1'

    def set_sms_info(self, key, msg_id, code, keep_time, success=True):
        hkey = RedisStr.SMSHKeyPtn % key
        logging.debug("set sms info by key[%s]: code[%s]" % (hkey, code))
        hdata = {
            RedisStr.SMSCodeField: code,
            RedisStr.SMSStatusField: '1' if success else '0',
            RedisStr.SMSIdFiled: msg_id
        }
        if self.r.hmset(hkey, hdata):
            return self.r.expire(hkey, keep_time)
        logging.warning("hmset sms info failed:key[%s], code[%d]" % (key, code))
        return False

    def remove_hobby(self, hobby_id):
        self.r.srem(RedisStr.HobbySKey, hobby_id)

    def add_hobby(self, hobby_id, hobby_str):
        self.r.sadd(RedisStr.HobbySKey, "%s:%s" % (hobby_id, hobby_str))

    def add_hobby_(self, hobby_id):
        self.r.sadd(RedisStr.HobbySKey, hobby_id)

    def get_app_version_info(self):
        res = self.r.hgetall(RedisStr.AppVersionHKey)
        return res

    def set_app_version_info(self, version_data, publish_data):
        p = self.r.pipeline()
        p.hset(RedisStr.AppConfigHKey, RedisStr.AppVersionConfField, version_data)
        p.publish(RedisStr.ConfigChannel, publish_data)
        res = p.execute()
        return res[1]

# coding: utf-8

import logging
import time

import tornado.gen

from model.cache.cache_define import RedisStr
from model.cache.cache_tools import atoi
from model.user_info import UserInfo
from utils.util_tools import get_star, make_key


class UserCenter(object):
    _field_mapping_ = {
        'nick_name': RedisStr.UserNickNameField,
        'signature': RedisStr.UserSignField,
        'avatar': RedisStr.UserAvatarField,
        'hobbies': RedisStr.UserHobbiesField,
        'show_pics': RedisStr.UserShowPicsField,
        'gender': RedisStr.UserGenderField,
        'born': RedisStr.UserBornDateField
    }

    def __init__(self, redis_conn, yx):
        self.r = redis_conn
        self.yunxin = yx
        self._cache_time = 10 * 60
        self.cache_fields = (
            RedisStr.UserNickNameField,
            RedisStr.UserSignField,
            RedisStr.UserAvatarField,
            RedisStr.UserGenderField,
            RedisStr.UserBornDateField,
            RedisStr.UserHobbiesField,
            RedisStr.UserShowPicsField
        )

    def user_gold(self, user_id):
        return atoi(self.r.zscore(RedisStr.UserTotalFortuneZKey, user_id))

    @tornado.gen.coroutine
    def reset_phone_user_password(self, country, phone, password):
        '''
        :param country:
        :param phone:
        :param password:
        :return: user id.
        '''
        key = make_key(country, phone)
        user_id = yield tornado.gen.Task(UserInfo.update_password_by_phone, key, password)
        raise tornado.gen.Return(user_id)

    @tornado.gen.coroutine
    def user_id_by_phone(self, country, phone):
        key = make_key(country, phone)
        user_id = yield tornado.gen.Task(UserInfo.get_id_by_phone, key)
        raise tornado.gen.Return(user_id)

    @tornado.gen.coroutine
    def add_phone_user(self, country_phone, password):
        ret = yield tornado.gen.Task(UserInfo.get_id_by_phone, country_phone)
        uid = 0
        if not ret:
            uid = yield tornado.gen.Task(UserInfo.add, country_phone, password)
        else:
            logging.info('user %s exist.', ret)
        raise tornado.gen.Return(uid)

    @tornado.gen.coroutine
    def add_wx_user(self, openid, unionid, device, refresh_token, refresh_time):
        '''
        :param openid:
        :param unionid:
        :param device:
        :param refresh_token:
        :param refresh_time:
        :return: user_id, is_new, is_banned
        '''
        user_id, already_exist, extra = yield tornado.gen.Task(
            UserInfo.wx_add_user, openid, unionid, device, refresh_token, refresh_time, '', '')
        # extra = (ban_st, avatar, sign, nick)
        ret = (user_id, not already_exist, extra[0])
        raise tornado.gen.Return(ret)

    @tornado.gen.coroutine
    def login_by_phone(self, country, phone, password):
        key = make_key(country, phone)
        usr = yield tornado.gen.Task(UserInfo.get_login_data, key, password)
        raise tornado.gen.Return(usr)

    @tornado.gen.coroutine
    def update_user(self, uid, **kwargs):
        '''
        :param uid: user id
        :param nick_name: user nick name
        :param signature: user signature
        :param avatar: user avatar url
        :param hobbies: user hobby list
        :param show_pics: user picture in wall
        :param gender: user gender: 1 male, 0 female.
        :param born: user born, ie: 1992-03-22
        :return:
        '''
        user = UserInfo(**kwargs)
        user.user_id = uid
        if user.born:
            t = time.strptime(user.born, '%Y-%m-%d')
            user.star = get_star(t.tm_mon, t.tm_mday)
        ret = yield tornado.gen.Task(user.update_to_db)
        success = ret is not None
        if success:
            data = {self._field_mapping_[k]: v for k, v in kwargs.iteritems()}
            user_level = self._update_user(uid, data)
            response = yield tornado.gen.Task(self.yunxin.update_user_card, uid, level=user_level, **kwargs)
            if not response:
                logging.warning('update user card failed.')
        raise tornado.gen.Return(success)

    @tornado.gen.coroutine
    def get_users(self, uid_list, ensure_order=True):
        '''
        :param uid_list: ["1", "2"]
        :param ensure_order: make result ordered.
        :return:
        '''
        p = self.r.pipeline()
        for uid in uid_list:
            p.hmget(RedisStr.UserHKeyPtn % uid, self.cache_fields)
        ret = p.execute()
        users = []
        missed = {}
        for i, cached_data in enumerate(ret):
            if cached_data:
                users.append(self._gen_user_from_cache(uid_list[i], cached_data))
            else:
                if ensure_order:
                    users.append(None)
                missed[uid_list[i]] = i
        success, db_users = yield tornado.gen.Task(
            UserInfo.get_specified_rows, missed.iterkeys())
        if success:
            for user in db_users:
                self._cache_user(user)
                if ensure_order:
                    users[missed[str(user.user_id)]] = user
                else:
                    users.append(user)
        else:
            logging.warning('get user from database failed.')
        raise tornado.gen.Return(users)

    @tornado.gen.coroutine
    def get_user(self, uid):
        ret = self.r.hmget(RedisStr.UserHKeyPtn % uid, self.cache_fields)
        if not ret:
            user = yield tornado.gen.Task(UserInfo.get_one, uid)
            if user:
                self._cache_user(user)
        else:
            user = self._gen_user_from_cache(uid, ret)
        raise tornado.gen.Return(user)

    def _gen_user_from_cache(self, uid, cached_data):
        return UserInfo(
            user_id=uid,
            avatar=cached_data[2],
            signature=cached_data[1],
            nick_name=cached_data[0],
            gender=cached_data[3],
            born=cached_data[4],
            hobbies=cached_data[5],
            show_pics=cached_data[6]
        )

    def _cache_user(self, user):
        p = self.r.pipeline()
        key = RedisStr.UserInfoCacheHKeyPtn % user.user_id
        p.hmset(key, {
            RedisStr.UserNickNameField: user.nick_name,
            RedisStr.UserSignField: user.signature,
            RedisStr.UserAvatarField: user.avatar,
            RedisStr.UserGenderField: user.gender,
            RedisStr.UserBornDateField: user.born,
            RedisStr.UserHobbiesField: user.hobbies,
            RedisStr.UserShowPicsField: user.show_pics
        })
        p.expire(key, self._cache_time)
        p.execute()

    def _update_user(self, user_id, data):
        p = self.r.pipeline()
        p.hmset(RedisStr.UserHKeyPtn % user_id, data)
        p.hmset(RedisStr.UserInfoCacheHKeyPtn % user_id, data)
        p.hget(RedisStr.UserHKeyPtn % user_id, RedisStr.UserVipLevelField)
        ret = p.execute()
        return int(ret[1]) if ret[1] else 1

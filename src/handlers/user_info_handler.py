# coding: utf-8

import logging
from functools import partial

import tornado.gen

from handlers.base_handler import KVBaseHandler, CoroutineBaseHandler
from model.user_info import UserInfo
from model.cache.user_info_cache import UserInfoCache
from model.response import Status
from model.response import Strings
from model.response import UserDetail
from model.response import UserVisitors
from model.response import UsersMetaInfo
from utils.common_define import ErrorCode, HttpErrorStatus
from utils.repoze.lru import ExpiringLRUCache
from utils.util_tools import make_force_offline_msg


class GetUserLocationHandler(KVBaseHandler):
    def do_post(self):
        ids = self.get_argument('users')
        if len(ids) > 500:
            self.set_status(*HttpErrorStatus.WrongParams)
        else:
            strs = Strings()
            strs.data = self.application.redis_wrapper.get_cache(UserInfoCache.cache_name).get_users_location(ids)
            self.write_response(strs)
        self.finish()


class GetUserInfoHandler(KVBaseHandler):
    users_cache = ExpiringLRUCache(1000, 60)

    def do_post(self):
        ids = self.get_argument('users').strip()
        id_list = ids.split(',')
        if len(id_list) > 50 or not id_list:
            self.set_status(*HttpErrorStatus.WrongParams)
            self.finish()
            return
        result = UsersMetaInfo()
        user_for_db = self.application.get_cache(UserInfoCache.cache_name).get_users_meta_info(id_list, result)

        if user_for_db:
            self.application.async_db.get_user_info_by_list(
                [str(i) for i in user_for_db.keys()], partial(self.on_finish_get_user_info, result, user_for_db))
        else:
            self.write_response(result)
            self.finish()

    def on_finish_get_user_info(self, result, user_for_db, resp):
        if not resp.error and resp.body:
            db_res = UsersMetaInfo()
            db_res.ParseFromString(resp.body)
            for usr in db_res.users:
                u = user_for_db[usr.id]
                u.avatar = self.application.qiniu_api.get_pub_url(usr.avatar)
                usr.avatar = u.avatar
                u.nickName = usr.nickName
                u.isMale = usr.isMale
                u.signature = usr.signature
            self.application.get_cache(UserInfoCache.cache_name).update_users_info(db_res)
        else:
            logging.warning('get user meta info from db failed:[%s]' % resp.body)
        self.write_response(result)
        self.finish()


class GetUsersDetailHandler(CoroutineBaseHandler):
    @tornado.gen.coroutine
    def do_post(self, *args):
        id_list = self.get_argument('users')
        locations, status = self.application.get_cache(UserInfoCache.cache_name).get_users_status(id_list)
        users_detail = yield tornado.gen.Task(UserInfo.get_users_detail, (str(uid) for uid in id_list))
        result = UserVisitors()
        if users_detail:
            for i, user_id in enumerate(id_list):
                uinfo = users_detail.get(user_id, None)
                if uinfo:
                    visitor = result.add()
                    visitor.nickname = uinfo['nick_name']
                    visitor.sign = uinfo['signature']
                    visitor.birthday = uinfo['born'].strftime('%Y-%m-%d')
                    visitor.sex = uinfo['gender']
                    visitor.avatar = self.application.qiniu_api.get_pub_url(uinfo['avatar'])
                    visitor.star = uinfo['star']
                    visitor.location = locations[i]
                    visitor.isLiving = status[i]
                    visitor.userId = user_id
        self.write_response(result)
        self.finish()


class GetUserDetailHandler(KVBaseHandler):
    def do_post(self):
        user_id = int(self.get_argument('uid'))
        owner_id = int(self.get_argument('oid'))
        user_detail_pb = self.application.user_detail_cache.get(owner_id)
        cur_gold = self.visit_event(owner_id, user_id)
        if user_detail_pb:
            user_detail_pb.gold = cur_gold
            self.write_response(user_detail_pb)
            self.finish()
        else:
            self.application.async_db.get_user_detail(
                owner_id, partial(self.on_finish_get_user_detail, user_id, cur_gold))

    def on_finish_get_user_detail(self, uid, cur_gold, resp):
        if not resp.error and resp.body:
            user_detail_pb = UserDetail()
            user_detail_pb.ParseFromString(resp.body)
            # return avatar
            user_detail_pb.avatar = self.application.qiniu_api.get_pub_url(user_detail_pb.avatar)
            user_detail_pb.pics = self.application.qiniu_api.get_pub_urls(user_detail_pb.raw_pics)
            user_detail_pb.isAnchor, user_detail_pb.isLiving, user_detail_pb.location = \
                self.application.redis_wrapper.get_cache(UserInfoCache.cache_name).user_live_status(uid)
            user_detail_pb.gold = cur_gold
            self.application.user_detail_cache.put(user_detail_pb.id, user_detail_pb)
            self.write_response(user_detail_pb)
        else:
            self.set_status(*HttpErrorStatus.TargetNotExist)
        self.finish()

    def visit_event(self, owner_id, visitor_id):
        uif_cache = self.application.redis_wrapper.get_cache(UserInfoCache.cache_name)
        if owner_id != visitor_id and visitor_id:
            return uif_cache.add_visitors(owner_id, visitor_id)
        return uif_cache.get_user_gold(owner_id)


class GetUserVisitorsHandler(CoroutineBaseHandler):
    @tornado.gen.coroutine
    def do_post(self):
        user_id = self.get_argument('uid')
        start = int(self.get_argument('start'))
        size = int(self.get_argument('size'))

        visitors, locations, status = self.application.redis_wrapper.get_cache(UserInfoCache.cache_name).get_visitors(
            user_id, start, size) if start < 100 else []
        id_list = (v[0] for v in visitors)
        users_detail = yield tornado.gen.Task(UserInfo.get_users_detail, id_list)
        visit_data = UserVisitors()
        if users_detail:
            for i, visit_inf in enumerate(visitors):
                visitor_id = int(visit_inf[0])
                uinfo = users_detail.get(visitor_id, None)
                if uinfo:
                    visitor = visit_data.add()
                    visitor.nickname = uinfo['nick_name']
                    visitor.sign = uinfo['signature']
                    visitor.birthday = uinfo['born'].strftime('%Y-%m-%d')
                    visitor.sex = uinfo['gender']
                    visitor.avatar = self.application.qiniu_api.get_pub_url(uinfo['avatar'])
                    visitor.star = uinfo['star']
                    visitor.location = locations[i]
                    visitor.isLiving = status[i]
                    visitor.userId, visitor.visitTime = visit_inf
        self.write_response(visit_data)
        self.finish()


class ModifyUser(CoroutineBaseHandler):
    VALID_GENDER_LIST = ["0", "1", None]

    def _ez_arg(self, key, dest_key, ret, process_func=None):
        val = self.get_argument(key, None)
        if val is not None:
            ret[dest_key] = process_func(val) if process_func else val

    @tornado.gen.coroutine
    def do_post(self):
        uid = self.get_argument("uid")
        kwargs = {}
        qn = self.application.qiniu_api
        self._ez_arg('nick', 'nick_name', kwargs)
        self._ez_arg('avatar', 'avatar', kwargs, lambda at: qn.get_pub_url(at))
        self._ez_arg('sign', 'signature', kwargs)
        self._ez_arg('born', 'born', kwargs)
        self._ez_arg('pics', 'show_pics', kwargs, lambda pics: ','.join(qn.get_pub_urls(pics)))
        self._ez_arg('gender', 'gender', kwargs)
        if not kwargs:
            self.set_status(*HttpErrorStatus.WrongParams)
            self.finish()
            return
        ret = Status()
        ret.success = yield self.application.user_center.update_user(uid, **kwargs)
        if not ret.success:
            ret.code = ErrorCode.ServerError
        self.write_response(ret)
        self.finish()


class SelectHobby(KVBaseHandler):
    def do_post(self):
        '''hobbies is merge through: bobby1 ^ hobby2 ^ hobby3...'''
        uid = self.get_argument("uid")
        hb_list = self.get_argument('hobbies')
        self.application.async_db.add_hobby_to_user(uid, hb_list, self.on_finish_add_hobby)

    def on_finish_add_hobby(self, resp):
        ret = Status()
        if resp.error or resp.body != 'OK':
            ret.success = False
            ret.code = ErrorCode.ServerError
        self.write_response(ret)
        self.finish()


class ResetPasswordHandler(CoroutineBaseHandler):
    @tornado.gen.coroutine
    def do_post(self):
        country = self.get_argument('country')
        phone = self.get_argument('phone')
        pwd = self.get_argument('pwd')
        result = Status()
        result.success = False
        if len(pwd) == 32:
            user_id = yield self.application.user_center.reset_phone_user_password(country, phone, pwd)
            if result:
                imei = self.get_argument('imei')
                cache = self.application.get_cache(UserInfoCache.cache_name)
                token_data = cache.get_user_token(user_id)
                logging.debug('got token data:[%s]-[%s]', token_data.token, token_data.machine)
                if token_data.token and token_data.machine != imei:
                    logging.debug('user has login on other machine:[%s]', token_data.machine)
                    # 无效老的token
                    cache.invalid_token(user_id)
                    # 通知当前登录的用户
                    self.application.async_im.push_msg_to_user(
                        user_id, user_id, make_force_offline_msg(),
                        lambda resp: (not resp) or logging.warning(
                            'notify user[{}] force leave message failed.'.format(user_id)))
                result.success = True
            else:
                result.code = ErrorCode.ServerError
        else:
            result.code = ErrorCode.InvalidParam
        self.write_response(result)


class GetUserGoldHandler(KVBaseHandler):
    def do_post(self):
        ret = Status()
        gold = self.application.user_center.user_gold(self.current_user)
        ret.data = gold
        self.write_response(ret)
        self.finish()

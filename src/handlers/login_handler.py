# coding: utf-8
import logging
import uuid

import tornado.gen
import tornado.ioloop
from model.cache.user_info_cache import UserInfoCache

import celeryapp.tasks as CeleryTasks
from handlers.base_handler import KVBaseHandler, CoroutineBaseHandler
from model.tableconstant import USER_BANNED
from model.cache.server_cache import ServerCache
from model.response import Status, LoginInfo, WxLoginInfo
from utils.common_define import ErrorCode
from utils.util_tools import make_key, encode_token

max_nick_len = 16
wechat_tag = 'WX'


def gen_sys_token(user_id):
    sys_token = str(uuid.uuid1()).replace('-', '')
    encoded_sys_token = encode_token('{}-{}'.format(user_id, sys_token))
    return sys_token, encoded_sys_token


def adjust_user_nick_name(src):
    if not isinstance(src, unicode):
        src = src.decode('utf-8')
    real_len = 0
    out = []
    for ch in src:
        ch_len = len(ch.encode('utf-8'))
        if ch_len == 1:
            real_len += 1
        elif ch_len == 3:
            real_len += 2
        else:
            real_len += 4
        if real_len > max_nick_len:
            out.append('...')
            break
        out.append(ch)
    return ''.join(out)


class UserLoginHandler(CoroutineBaseHandler):
    @tornado.gen.coroutine
    def do_post(self):
        cur_usr, _ = self._extract_user()
        if not cur_usr:
            country = self.get_argument("country")
            phone = self.get_argument("phone")
            pw = self.get_argument("pwd")
            user = yield self.application.user_center.login_by_phone(country, phone, pw)
            yield self.login_with_password(user)
        else:
            result = LoginInfo()
            imei = self.get_argument('imei')
            user_id = result.userId = cur_usr
            user_cache = self.application.get_cache(UserInfoCache.cache_name)
            yx_token, sys_token_data = user_cache.process_user_login(user_id)
            if not yx_token:
                yield self.do_refresh_token(user_id, result, user_cache)
            else:
                result.yxToken = yx_token
                if sys_token_data.token and imei != sys_token_data.machine:
                    logging.debug('got token[{}] on machine [{}]'.format(sys_token_data.token, sys_token_data.machine))
                    result.errCode = ErrorCode.LoginByOtherMachine
            self.write_response(result)

    @tornado.gen.coroutine
    def login_with_password(self, user):
        result = LoginInfo()
        result.success = False
        if not user:
            result.errCode = ErrorCode.IncorrectPassword
        elif user.ban_status == USER_BANNED:
            result.errCode = ErrorCode.UserBanned
        else:
            result.userId = user.user_id
            result.nickname = user.nick_name
            result.avatar = user.avatar
            result.sign = user.signature
            result.born = user.born.strftime('%Y-%m-%d')
            result.hobbies = user.hobbies
            result.gender = user.gender
            result.pics = user.show_pics
            yield self.process_login_info(result)
        self.write_response(result)

    @tornado.gen.coroutine
    def process_login_info(self, result):
        imei = self.get_argument('imei')
        ip = self.get_argument('ip')
        user_id = result.userId
        user_cache = self.application.redis_wrapper.get_cache(UserInfoCache.cache_name)
        yx_token, sys_token_data = user_cache.process_user_login(user_id)
        if yx_token:
            result.yxToken = yx_token
            if sys_token_data.token and imei != sys_token_data.machine:
                logging.debug('got token[%s] on machine [%s]', sys_token_data.token, sys_token_data.machine)
                result.errCode = ErrorCode.LoginByOtherMachine
                result.success = False
            sys_token = str(uuid.uuid1()).replace('-', '')
            user_cache.update_user_token(user_id, sys_token, imei)
            result.sysToken = encode_token('{}-{}'.format(user_id, sys_token))
            CeleryTasks.user_login.apply_async(args=(user_id, imei, ip, self.get_argument('site')))
            result.success = True
        else:
            yield self.do_refresh_token(user_id, result, user_cache)

    @tornado.gen.coroutine
    def do_refresh_token(self, user_id, result, user_cache):
        err_code, data = yield self.application.async_im.refresh_token(user_id)
        if not err_code:
            result.yxToken = data
            logging.debug('update user %s token with %s', user_id, data)
            user_cache.update_yx_token(user_id, data)
        else:
            result.success = False
            result.errCode = ErrorCode.ThirdPartyError
            CeleryTasks.refresh_yx_token_failed.apply_async(args=(user_id, err_code, data))


class SendRegisterVerifyCodeHandler(CoroutineBaseHandler):
    _sms_code_expire_time_ = 60
    ''' send sms code'''

    @tornado.gen.coroutine
    def do_post(self):
        country = self.get_argument("country")
        phone = self.get_argument("phone")
        key = make_key(country, phone)
        result = Status()
        result.success = False
        user_exist = self.application.get_cache(UserInfoCache.cache_name).is_user_exist(key) is not None
        if user_exist and not self.user_required:
            result.code = ErrorCode.UserExist
        else:
            user_id = yield self.application.user_center.user_id_by_phone(country, phone)
            server_cache = self.application.get_cache(ServerCache.cache_name)
            if user_id and not self.user_required:
                result.code = ErrorCode.UserExist
            elif not user_id and self.user_required:
                result.code = ErrorCode.UserNotExist
            elif server_cache.sms_already_send(key):
                result.code = ErrorCode.SendSMSOver
            else:
                err_code, vcode = yield self.application.async_im.send_sms(phone)
                self.process_send_sms_result(key, err_code, vcode, result)
        self.write_response(result)

    @property
    def user_required(self):
        return False

    def process_send_sms_result(self, key, err_code, vcode, result):
        if not err_code:
            logging.debug('send sms success, code: [%s]', vcode)
            self.application.get_cache(ServerCache.cache_name).set_sms_info(
                key, '', vcode, self._sms_code_expire_time_)
            result.success = True
        else:
            result.code = ErrorCode.SendSMSFailed


class SendResetPwVerifyCodeHandler(SendRegisterVerifyCodeHandler):
    @property
    def user_required(self):
        return True


class ValidateSMSCode(KVBaseHandler):
    ''' Check code is the same with redis '''

    def do_post(self):
        country = self.get_argument("country")
        phone = self.get_argument("phone")
        code = self.get_argument("code")
        phone_key = make_key(country, phone)
        correct_sms_code = self.application.get_cache(ServerCache.cache_name).get_sms_code(phone_key)

        result = Status()
        result.success = correct_sms_code == code
        if not result.success:
            result.code = ErrorCode.IncorrectSMSCode
        self.write_response(result)
        self.finish()


class RegisterUser(CoroutineBaseHandler):
    @tornado.gen.coroutine
    def do_post(self):
        country = self.get_argument("country")
        phone = self.get_argument("phone")
        pwd = self.get_argument("pwd")
        sms_code = self.get_argument('code')

        result = Status()
        phone_key = make_key(country, phone)
        correct_sms_code = self.application.get_cache(ServerCache.cache_name).get_sms_code(phone_key)
        if correct_sms_code == sms_code:
            user_id = yield self.application.user_center.add_phone_user(phone_key, pwd)
            if not user_id:
                result.success = False
                result.code = ErrorCode.UserExist
            else:
                result.code = user_id
                err_code, token = yield self.application.async_im.create_user_coroutine(user_id, user_id, '')
                if not err_code:
                    self.application.get_cache(UserInfoCache.cache_name).set_user_yunxin_token(user_id, token)
                else:
                    CeleryTasks.create_yx_user_failed.apply_async(args=(user_id, err_code, token))
        else:
            result.success = False
            result.code = ErrorCode.IncorrectSMSCode
        self.write_response(result)


class WeChatUserLoginHandler(CoroutineBaseHandler):
    @tornado.gen.coroutine
    def do_post(self, *args):
        code = self.get_argument('code')
        result = WxLoginInfo()
        ac_tool = self.application.tecent_access_tool
        token_data = yield ac_tool.get_wx_access_token(code)
        if token_data:
            user_info = yield ac_tool.get_wx_user_info(token_data.access_token, token_data.openid)
            yield self.process_wx_user(token_data, result, user_info)
        else:
            logging.warning('get access token failed with code:{}'.format(self.get_argument('code')))
            self.end_bad_story(result, ErrorCode.ThirdPartyError)

    @tornado.gen.coroutine
    def process_wx_user(self, token_data, result, user_info):
        if user_info:
            device = self.get_argument('dvc')
            nick_name = adjust_user_nick_name(user_info.nickname)
            avatar = user_info.headimgurl
            result.nickname = nick_name
            result.avatar = avatar
            uid, is_new, is_banned = yield self.application.user_center.add_wx_user(
                user_info.openid, user_info.unionid, device, token_data.refresh_token, token_data.time)
            result.userId = uid
            # create user over, create user to yunxin
            if result.userId:
                result.success = True
                if is_new:
                    err_code, token = yield self.application.async_im.create_user_coroutine(
                        result.userId, result.nickname, result.avatar)
                    self.process_new_wx_user(err_code, token, result)
                else:
                    yield self.process_old_wx_user(is_banned, result)
                CeleryTasks.user_login.apply_async(args=(
                    uid, self.get_argument('dvc'), self.get_argument('ip'), self.get_argument('site')))
            else:
                self.end_bad_story(result, ErrorCode.DatabaseError)
        else:
            self.end_bad_story(result, ErrorCode.ThirdPartyError)

    def end_bad_story(self, result, code):
        result.success = False
        result.errCode = code
        self.write_response(result)

    def process_new_wx_user(self, err_code, token, result):
        if not err_code:
            ip = self.get_argument('ip')
            sys_token, result.sysToken = gen_sys_token(result.userId)
            result.yxToken = token
            device = self.get_argument('dvc')
            self.application.get_cache(UserInfoCache.cache_name).update_user_tokens_device(
                result.userId, token, sys_token, device, device, wechat_tag)
            self.write_response(result)
        else:
            CeleryTasks.create_yx_user_failed.apply_async(args=(result.userId, err_code, token))
            self.end_bad_story(result, ErrorCode.ThirdPartyError)

    @tornado.gen.coroutine
    def process_old_wx_user(self, ban_st, result):
        if ban_st != USER_BANNED:
            ip = self.get_argument('ip')
            user_id = result.userId
            user_cache = self.application.get_cache(UserInfoCache.cache_name)
            sys_token, encoded_sys_token = gen_sys_token(user_id)
            device = self.get_argument('dvc')

            yx_token = user_cache.process_wx_user_login(user_id, sys_token, device, wechat_tag)
            result.sysToken = encoded_sys_token
            if yx_token:
                logging.debug('[wx]gen system token:%s, after encode:%s', sys_token, result.sysToken)
                result.yxToken = yx_token
            else:
                logging.debug('yx token not exist, recreate it.')
                err_code, token = yield self.application.async_im.create_user_coroutine(user_id, user_id, '')
                if not err_code:
                    logging.debug('create yunxin account for user[%s] success.', result.userId)
                    result.yxToken = token
                    user_cache.update_yx_token(result.userId, result.yxToken)
                else:
                    CeleryTasks.create_yx_user_failed.apply_async(args=(result.userId, err_code, token))
                    result.success = False
                    result.errCode = ErrorCode.ThirdPartyError
        else:
            result.success = False
            result.errCode = ErrorCode.UserBanned
        self.write_response(result)


class UserOfflineHandler(KVBaseHandler):
    def do_post(self):
        self.application.get_cache(UserInfoCache.cache_name).invalid_token(self.current_user)
        out = Status()
        out.success = True
        self.write_response(out)
        self.finish()

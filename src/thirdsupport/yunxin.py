# coding: utf-8
from tornado.httpclient import HTTPRequest
from tornado.httpclient import AsyncHTTPClient
import json
import logging
import random
import datetime
import hashlib
import urllib
import time
import uuid
import tornado.gen


class YunXinJsonTag(object):
    ChatRoom = 'chatroom'
    RoomId = 'roomid'
    Valid = 'Valid'


class YunXinRequestBase(object):
    DEFAULT_CONTENT_TYPE = 'application/x-www-form-urlencoded;charset=utf-8'

    def __init__(self, app_key, app_secret, content_type=None):
        self.app_key = app_key
        self.app_secret = app_secret
        self.content_type = content_type if content_type is not None else self.DEFAULT_CONTENT_TYPE

    def make_header(self):
        nonce = str(random.randint(1, 1000000))
        cur_time = str(int(time.mktime(datetime.datetime.now().timetuple())))
        check_sum = hashlib.sha1('%s%s%s' % (self.app_secret, nonce, cur_time)).hexdigest()
        headers = [
            ('AppKey', self.app_key),
            ('Nonce', nonce),
            ('CurTime', cur_time),
            ('CheckSum', check_sum),
            ('Content-Type', self.content_type)
        ]
        return headers


class YunXinAPI(YunXinRequestBase):
    def __init__(self, app_key, app_secret, host, super_user):
        super(YunXinAPI, self).__init__(app_key, app_secret)
        self.super_user = super_user
        self.HOST = host
        self.create_user_url = '%s/nimserver/user/create.action' % self.HOST
        self.update_user_url = '%s/nimserver/user/update.action' % self.HOST
        self.refresh_token_url = '%s/nimserver/user/refreshToken.action' % self.HOST
        self.block_token_url = '%s/nimserver/user/block.action' % self.HOST
        self.unblock_user_url = '%s/nimserver/user/unblock.action' % self.HOST
        self.update_user_card_url = '%s/nimserver/user/updateUinfo.action' % self.HOST
        self.set_push_rule_url = '%s/nimserver/user/setDonnop.action' % self.HOST
        self.add_friend_url = '%s/nimserver/friend/add.action' % self.HOST
        self.remark_friend_url = '%s/nimserver/friend/update.action' % self.HOST
        self.remove_friend_url = '%s/nimserver/friend/delete.action' % self.HOST
        self.friend_list_url = '%s/nimserver/friend/get.action' % self.HOST
        self.relation_operation_url = '%s/nimserver/user/setSpecialRelation.action' % self.HOST
        self.relation_query_url = '%s/nimserver/user/listBlackAndMuteList.action' % self.HOST
        self.send_normal_msg_url = '%s/nimserver/msg/sendMsg.action' % self.HOST
        self.push_msg_url = '%s/nimserver/msg/sendAttachMsg.action' % self.HOST
        self.send_sms_url = '%s/sms/sendcode.action' % self.HOST
        self.verify_sms_url = '%s/sms/verifycode.action' % self.HOST
        self.create_chat_room_url = '%s/nimserver/chatroom/create.action' % self.HOST
        self.send_msg_2_chat_room_url = '%s/nimserver/chatroom/sendMsg.action' % self.HOST
        self.set_chatroom_role_url = '%s/nimserver/chatroom/setMemberRole.action' % self.HOST
        self.get_user_info_url = '%s/nimserver/user/getUinfos.action' % self.HOST
        self.get_chatroom_info_url = '%s/nimserver/chatroom/get.action' % self.HOST

    def callback_wrapper(self, notice, callback):
        def func(resp):
            if resp.error:
                callback(None)
            else:
                try:
                    obj = json.loads(resp.body)
                    if obj['code'] != 200:
                        logging.warning('received bad code for [%s], response[%s]' % (notice, resp.body))
                        callback(None)
                    else:
                        callback(obj)
                except Exception:
                    logging.exception('parse response[%s] for [%s] failed.' % (resp.body, notice))
                    callback(None)

        return func

    def easy_request(self, url, notice, callback, **kwargs):
        params = {}
        for k, v in kwargs.items():
            if v is not None:
                params[k] = v
        req_param = urllib.urlencode(params)
        hds = self.make_header()
        req = HTTPRequest(url=url, body=req_param, headers=hds, method='POST')
        AsyncHTTPClient().fetch(req, self.callback_wrapper(notice, callback), raise_error=False)

    def create_user(self, user_id, nick_name, token, avatar, other_json, callback):
        self.easy_request(self.create_user_url, 'create user[%s]' % user_id, callback,
                          accid=user_id, name=nick_name, token=token, icon=avatar, props=other_json)

    @tornado.gen.coroutine
    def create_user_coroutine(self, user_id, nick_name, avatar):
        param = urllib.urlencode({'accid': user_id, 'name': nick_name, 'icon': avatar})
        request = HTTPRequest(url=self.create_user_url, body=param, headers=self.make_header(), method='POST')
        response = yield AsyncHTTPClient().fetch(request)
        ret = self._parser_response(response, lambda obj: obj['info']['token'])
        raise tornado.gen.Return(ret)

    def update_user(self, user_id, props, token, callback):
        self.easy_request(self.update_user_url, 'update user[%s]' % user_id, callback,
                          accid=user_id, token=token, props=props)

    @tornado.gen.coroutine
    def refresh_token(self, user_id):
        param = "accid={}".format(user_id)
        headers = self.make_header()
        request = HTTPRequest(url=self.refresh_token_url, body=param, headers=headers, method='POST')
        response = yield AsyncHTTPClient().fetch(request)
        ret = self._parser_response(response, lambda obj: obj['info']['token'])
        raise tornado.gen.Return(ret)

    def kill_user(self, user_id, force_offline, callback):
        self.easy_request(self.block_token_url, 'kill user[%s]' % user_id, callback,
                          accid=user_id, needkick=force_offline)

    def update_user_card(self, user_id, **kwargs):
        nick_name = kwargs.get('nick_name', None)
        level = kwargs.get('level', None)
        if nick_name:
            if level is None:
                logging.warning("give up update nick_name, reason: not set user level")
                nick_name = None
            else:
                nick_name = '{}-{}'.format(level, nick_name)
        self.easy_request(self.update_user_card_url, 'update user[%s] card' % user_id,
                          kwargs.get('callback', None), accid=user_id, name=nick_name,
                          icon=kwargs.get('avatar', None), sign=kwargs.get('signature', None),
                          birth=kwargs.get('born', None), gender=kwargs.get('gender', None))

    def msg_push(self, user_id, unpush_desktop_online, callback):
        self.easy_request(self.set_push_rule_url, 'set push setting for user[%s]' % user_id, callback,
                          accid=user_id, donnopOpen=unpush_desktop_online)

    def add_friend(self, user_id, friend_id, req_type, req_msg, callback):
        '''
        @:param req_type:[1|2|3|4],
        1: add friend indirectly, 2: request to make friend, 3: agree to make friend, 4: reject to make friend
        @:param req_msg: message for making friend.
        '''
        self.easy_request(self.add_friend_url, 'add friend[%s]->[%s]' % (user_id, friend_id), callback,
                          accid=user_id, faccid=friend_id, type=req_type, msg=req_msg)

    def remark_friend(self, user_id, friend_id, remark_name, callback):
        self.easy_request(self.remark_friend_url, 'remark friend[%s]->[%s]' % (user_id, friend_id), callback,
                          accid=user_id, faccid=friend_id, alias=remark_name)

    def remove_friend(self, user_id, friend_id, callback):
        self.easy_request(self.remove_friend_url, 'remove friend[%s]->[%s]' % (user_id, friend_id), callback,
                          accid=user_id, faccid=friend_id)

    def get_friend_list(self, user_id, start_time, callback):
        '''@:param start_time: timestamp with seconds by utc.'''
        self.easy_request(self.friend_list_url, 'get friend list[%s]' % user_id, callback,
                          accid=user_id, createtime=start_time)

    def operate_blacklist(self, user_id, target_id, move_to_blacklist, callback):
        self.easy_request(self.relation_operation_url, 'blacklist [%s]->[%s]' % (user_id, target_id), callback,
                          accid=user_id, targetAcc=target_id, relationType='1', value='1' if move_to_blacklist else '0')

    def operate_mute(self, user_id, target_id, mute_user, callback):
        self.easy_request(self.relation_operation_url, 'mute [%s]->[%s]' % (user_id, target_id), callback,
                          accid=user_id, targetAcc=target_id, relationType='0', value='1' if mute_user else '0')

    def query_black_and_mute_list(self, user_id, callback):
        self.easy_request(self.relation_query_url, 'query black and mute list [%s]' % user_id, callback, accid=user_id)

    def send_normal_msg_to_user(self, source_id, target_id, msg_type, msg_body, callback):
        kwargs = {
            'from': source_id,
            'ope': '0',
            'to': target_id,
            'type': msg_type,
            'body': msg_body
        }
        self.easy_request(self.send_normal_msg_url, 'send msg[%s]->[%s]' % (source_id, target_id), callback, **kwargs)

    @tornado.gen.coroutine
    def send_sms(self, phone):
        param = "mobile={}".format(phone)
        request = HTTPRequest(url=self.send_sms_url, body=param, headers=self.make_header(), method='POST')
        response = yield AsyncHTTPClient().fetch(request)
        ret = self._parser_response(response, lambda obj: obj['obj'])
        raise tornado.gen.Return(ret)

    def verify_sms_code(self, phone, code, callback):
        self.easy_request(self.verify_sms_url, 'verify phone[%s] with code[%s]' % (phone, code), callback,
                          mobile=phone, code=code)

    def push_msg_to_user(self, source_id, target_id, msg_body, callback):
        kwargs = {
            'from': source_id,
            'msgtype': '0',
            'to': target_id,
            'attach': msg_body,
            'option': '{"badge":false}'
        }
        self.easy_request(self.push_msg_url, 'push msg [%s]->[%s]' % (source_id, target_id), callback, **kwargs)

    @tornado.gen.coroutine
    def notify_user(self, source_id, target_id, msg_body):
        param = urllib.urlencode({
            'from': source_id,
            'msgtype': '0',
            'to': target_id,
            'attach': msg_body,
            'option': '{"badge":false}'
        })
        request = HTTPRequest(url=self.push_msg_url, body=param, headers=self.make_header(), method='POST')
        response = yield AsyncHTTPClient().fetch(request)
        ret = self._parser_response(response, lambda obj: None)
        raise tornado.gen.Return(ret)

    def create_chatroom(self, usr_id, callback):
        chat_room_name = "%d_%s" % (int(time.time() * 1000), usr_id)
        self.easy_request(
            self.create_chat_room_url, 'create chat room[%s].' % chat_room_name, callback, creator=usr_id,
            name=chat_room_name)

    def set_user_role_in_chatroom(self, room_id, user_id, role_type, reset, callback):
        '''
        :param role_type:1, manager; 2, normal user; -1, blacklist user; -2, muted user.
        :param reset: true, confirm it; false, cancel it.
        '''
        self.easy_request(
            self.set_chatroom_role_url, 'set user[%s] role to [%s] in room %s' % (user_id, role_type, room_id),
            callback, roomid=room_id, operator=self.super_user, target=user_id, opt=role_type,
            optvalue='true' if reset else 'false')

    def send_msg_to_chatroom(self, room_id, ext, callback):
        '''
        :param ext: (msg_type, msg_string)
        :return:
        '''
        self.easy_request(self.send_msg_2_chat_room_url, 'sed msg to room[%s]' % room_id, callback,
                          roomid=room_id, msgId=uuid.uuid1(), fromAccid=self.super_user, msgType=100, resendFlag=0,
                          attach='{}', ext=json.dumps({'kind': ext[0], 'val': ext[1]}, separators=(',', ":")))

    def get_user_info(self, uid, callback):
        self.easy_request(self.get_user_info_url, 'get user[%s] info' % uid, callback, accids='["%s"]' % uid)

    def get_chat_room_info(self, room_id, callback):
        self.easy_request(self.get_chatroom_info_url, 'get chat room[%s] ino' % room_id, callback, roomid=room_id,
                          needOnlineUserCount='true')

    def _parser_response(self, response, extra_func):
        '''
        :param response:
        :param extra_func:
        :return: (errcode, data),
        errcode=0: no error. data=extra_func(obj)
        otherwise, data is error information.
        '''
        if not response.error:
            try:
                obj = json.loads(response.body)
                if obj['code'] != 200:
                    logging.warning('received bad code , response[%s]', response.body)
                    ret = (obj['code'], obj.get('desc', 'Unknown'))
                else:
                    ret = (0, extra_func(obj))
            except Exception, e:
                logging.exception('parse response[%s] failed.', response.body)
                ret = (1, str(e))
        else:
            ret = (response.code, response.reason)
        return ret

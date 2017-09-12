# coding: utf-8

import logging
import time
import tornado.gen
import tornado.httpclient
import tornado.web

from model.response.coredata import Status
from handlers.base_handler import KVBaseHandler, CoroutineBaseHandler
from model.cache import LiveCache
from model.response.livedata import CurrentLiving, CreateLiveResult, LiveDetail, RankData
from thirdsupport.live_requests import LiveJsonTag
from thirdsupport.yunxin import YunXinJsonTag
from utils.common_define import HttpErrorStatus


class GetLiveListHandler(CoroutineBaseHandler):
    _cache_ = [None, 0]

    @tornado.gen.coroutine
    def do_post(self, *args):
        uid = self.get_argument('uid')
        logging.info('user [{}] get live list'.format(uid))
        if not self._cache_[0] or time.time() > self._cache_[1]:
            result = CurrentLiving()
            self.application.get_cache(LiveCache.cache_name).get_live_list(result)
            users = yield self.application.user_center.get_users((item.ownerId for item in result.data))
            for i, user in enumerate(users):
                live_detail = result.data[i]
                live_detail.nick = user.nick_name
                live_detail.avatar = user.avatar
                live_detail.sign = user.signature
                live_detail.born = user.born
                live_detail.gender = user.gender
                live_detail.location = user.location
                live_detail.cover = user.avatar
            self._cache_[0] = result
            self._cache_[1] = time.time() + 1  # cache for 1 seconds.
        else:
            result = self._cache_[0]
        self.write_response(result)


class CreateLiveHandler(CoroutineBaseHandler):
    _push_url_expire_time_ = 100

    @tornado.gen.coroutine
    def do_post(self):
        uid = self.get_argument('uid')
        cover = self.get_argument('cov')
        title = self.get_argument('title')
        if uid == '0':
            self.set_status(*HttpErrorStatus.WrongParams)
            return

        result = CreateLiveResult()
        result.success = True
        self.application.get_cache(LiveCache.cache_name).create_live(uid, cover, title, result)

        resp = None
        if not result.pushUrl or not result.channelId:
            resp = yield self.process_create_live(uid, True, result)
        elif time.time() > result.expireTime:
            resp = yield self.process_create_live(uid, False, result)
        if result.success:
            if not result.chatRoomId:
                yield self.process_create_chat(uid, result)
            if result.success:
                logging.info('user [%s] started living', uid)
                # 创建成功, 开启直播
                self.application.live_biz.handle_start_live_event(uid, (
                    result.channelId,
                    result.pushUrl,
                    resp[LiveJsonTag.HttpPullUrl],
                    resp[LiveJsonTag.HlsPullUrl],
                    resp[LiveJsonTag.RtmpPullUrl],
                    result.expireTime
                ) if resp else None, result.chatRoomId)
                self.write_response(result)

    @tornado.gen.coroutine
    def process_create_chat(self, uid, result):
        chat_resp = yield tornado.gen.Task(self.application.async_im.create_chatroom, uid)
        if chat_resp:
            chat_room_id = chat_resp[YunXinJsonTag.ChatRoom][YunXinJsonTag.RoomId]
            result.chatRoomId = chat_room_id
            logging.info('create chat room[%s] for user[%s].', chat_room_id, uid)
        else:
            self.set_status(*HttpErrorStatus.SystemError)
            logging.warning('create chat room for user [%s] failed', uid)
            result.success = False
            self.write_response(result)

    @tornado.gen.coroutine
    def process_create_live(self, uid, is_new, result):
        logging.debug('process create live')
        live_api = self.application.async_live
        if is_new:
            live_channel_name = uid
            request = live_api.make_create_channel_request(live_channel_name)
        else:
            request = live_api.make_reset_channel_request(result.channelId)
        resp = yield tornado.httpclient.AsyncHTTPClient().fetch(request, raise_error=False)
        resp = live_api.parse_response(resp)
        if resp:
            resp = resp[LiveJsonTag.Result]
            result.pushUrl = resp[LiveJsonTag.PushUrl]
            cid = resp.get(LiveJsonTag.ChannelId, None)
            if cid:
                logging.info('create live[%s] for user[%s].' % (resp[LiveJsonTag.ChannelId], uid))
                result.channelId = cid
            result.expireTime = int(time.time()) + self._push_url_expire_time_
        else:
            self.set_status(*HttpErrorStatus.SystemError)
            logging.warning('create live channel for usr[%s] failed.' % uid)
            result.success = False
            self.write_response(result)
        logging.debug('process create live done.')
        raise tornado.gen.Return(resp)


class ResetLivePushAddrHandler(KVBaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        if not self.validate_request():
            self.set_status(*HttpErrorStatus.InvalidRequest)
            return
        channel_id = self.get_argument('cid')
        uid = self.get_argument('uid')
        logging.info('user[%s] reset live[%s] push url.' % (uid, channel_id))
        api = self.application.async_live
        request = api.make_refresh_push_addr_request(channel_id)
        resp = yield tornado.httpclient.AsyncHTTPClient().fetch(request, raise_error=False)
        resp = api.parse_response(resp)
        if not resp:
            logging.warning('reset push url failed.')
            self.set_status(*HttpErrorStatus.SystemError)
            return

        resp = resp[LiveJsonTag.Result]
        live_data = (
            channel_id,
            resp[LiveJsonTag.PushUrl],
            resp[LiveJsonTag.HttpPullUrl],
            resp[LiveJsonTag.HlsPullUrl],
            resp[LiveJsonTag.RtmpPullUrl]
        )
        live_cache = self.application.redis_wrapper.get_cache(LiveCache.cache_name)
        live_cache.update_live_settings(uid, live_data, None)
        result = Status()
        result.success = True
        result.data = live_data[1]
        self.write_response(result)


class GetLiveDetailHandler(KVBaseHandler):
    def do_post(self):
        uid = self.get_argument('uid')
        live_id = self.get_argument('liveid')
        result = LiveDetail()
        self.application.get_cache(LiveCache.cache_name).get_live_detail(uid, live_id, result)
        self.write_response(result)
        self.finish()


class RankHandler(CoroutineBaseHandler):
    @tornado.gen.coroutine
    def do_post(self, *args):
        live_id = self.get_argument('lid')
        size = int(self.get_argument('size', 20))
        rk_type = self.get_argument('type', 'D')
        cache = self.application.get_cache(LiveCache.cache_name)
        if rk_type == 'D':
            rank_data = cache.get_rank_data(live_id, size)
        else:
            rank_data = cache.get_rank_data(live_id, size, False)
        ret = RankData()
        users = (item[0] for item in rank_data)
        uinfos = yield self.application.user_center.get_users(users)
        for i, uinfo in enumerate(uinfos):
            usr = ret.data.add()
            usr.user_id = uinfo.user_id
            usr.avatar = uinfo.avatar
            usr.nick_name = uinfo.nick_name
            usr.contribution = int(rank_data[i][1])
        self.write_response(ret)

# coding: utf-8

import logging

import Geohash
import tornado.gen
from model.response import Status

import celeryapp.tasks as AsyncTasks
from handlers.base_handler import (KVBaseHandler, CoroutineBaseHandler)
from model.cache import GroundCache
from model.response.grounddata import ActivesStatistics
from utils.common_define import ErrorCode
from utils.util_tools import (get_geohash_precision_by_range, validate_position_pair)


class CreateActiveHandler(CoroutineBaseHandler):
    @tornado.gen.coroutine
    def do_post(self):
        result = Status()
        lon, lat = self.get_argument('lon'), self.get_argument('lat')
        if validate_position_pair(lon, lat):
            owner_id, topic_id = self.get_argument('oid'), self.get_argument('tid')
            body, pics = self.get_argument('text'), self.get_argument('pics')
            pics = ','.join(self.application.qiniu_api.get_pub_urls(pics))
            location = self.get_argument('site')
            geo_code = Geohash.encode(lat, lon)
            active_id = yield self.application.ground_center.add_active(
                owner_id, topic_id, body, pics, location, lon, lat, geo_code)
            if not active_id:
                result.code = ErrorCode.ServerError
                result.success = False
            else:
                result.code = active_id
        else:
            result.success = False
            result.code = ErrorCode.InvalidParam
        self.write_response(result)


class GetActivesHandler(CoroutineBaseHandler):
    @tornado.gen.coroutine
    def do_post(self):
        topic_id = self.get_argument('tid')
        user_id = self.get_argument('uid')
        start_id = int(self.get_argument('start', 0))
        want_new = self.get_argument('type', 'N') == 'N'  # N: new actives
        size = min(int(self.get_argument('size')), 20)
        result = yield self.application.ground_center.get_actives(user_id, topic_id, start_id, size, want_new)
        self.write_response(result)


class DeleteActiveHandler(CoroutineBaseHandler):
    @tornado.gen.coroutine
    def do_post(self):
        active_id = int(self.get_argument('aid'))
        user_id = int(self.get_argument('uid'))
        topic_id = int(self.get_argument('tid'))
        success = yield self.application.ground_center.del_active(topic_id, user_id)
        result = Status()
        if not success:
            result.success = False
            result.code = ErrorCode.ServerError
            logging.warning('delete active[{}] from db failed.'.format(active_id))
        self.write_response(result)


class LikeActiveHandler(KVBaseHandler):
    OP_TYPE = ['unlike', 'like']

    def do_post(self):
        active_id = self.get_argument('aid')
        active_owner_id = self.get_argument('auid')
        user_id = self.get_argument('uid')
        op_type = self.get_argument('op')
        summary = self.get_argument('summary')

        result = Status()
        result.success, result.data = False, int(active_id)
        # 1:like, 0: unlike
        do_like = self.OP_TYPE.index(op_type)
        cache = self.application.redis_wrapper.get_cache(GroundCache.cache_name)
        liked = cache.is_liked(user_id, active_id)
        if do_like and not liked:
            like_num, notified = cache.like_active(user_id, active_id, do_like)
            result.success = True
            result.code = like_num
            if not notified:
                AsyncTasks.push_like_message_to_user.apply_async(args=(active_owner_id, user_id, active_id, summary))
        elif not do_like and liked:
            like_num, notified = cache.like_active(user_id, active_id, do_like)
            result.success = True
            result.code = like_num
        elif do_like and liked:
            result.code = ErrorCode.AlreadyLiked
        else:
            result.code = ErrorCode.NotLiked
        AsyncTasks.like_active.apply_async(args=(user_id, active_id, do_like))
        self.write_response(result)
        self.finish()


class GetActiveMutableData(KVBaseHandler):
    def do_post(self):
        active_id_list = self.get_argument('actives').split(',')
        if active_id_list:
            actives_pb = ActivesStatistics()
            for aid in active_id_list:
                actives_pb.data.add().id = int(aid)
            self.application.redis_wrapper.get_cache(GroundCache.cache_name).get_actives_statistics(actives_pb)
            self.write_response(actives_pb)
        self.finish()


class AddCommentHandler(CoroutineBaseHandler):
    @tornado.gen.coroutine
    def do_post(self):
        topic_id = self.get_argument('topic')
        active_id = self.get_argument('aid')
        owner_id = self.get_argument('oid')
        tar_usr_id = self.get_argument('tuid')
        content = self.get_argument('text')
        summary = self.get_argument('ts')
        target_id = self.get_argument('tid')
        comment_id = yield self.application.ground_center.add_comment(
            topic_id, active_id, owner_id, target_id, tar_usr_id, content, summary)
        result = Status()
        if not comment_id:
            result.success = False
            result.code = ErrorCode.DatabaseError
        self.write_response(result)


class DeleteCommentHandler(CoroutineBaseHandler):
    @tornado.gen.coroutine
    def do_post(self):
        comment_id = self.get_argument('cid')
        active_id = self.get_argument('aid')
        success = yield self.application.ground_center.del_comment(active_id, comment_id)
        result = Status()
        if not success:
            result.success = False
            result.code = ErrorCode.DatabaseError
        self.write_response(result)


class GetActiveCommentsHandler(CoroutineBaseHandler):
    @tornado.gen.coroutine
    def do_post(self):
        active_id = self.get_argument('aid')
        size = min(int(self.get_argument('size', 20)), 30)
        offset = int(self.get_argument('start', 0))
        ret = yield self.application.ground_center.get_active_comments(active_id, offset, size)
        self.write_response(ret)


class GetActivesNearbyEpHandler(CoroutineBaseHandler):
    @tornado.gen.coroutine
    def do_post(self):
        user_id = self.get_argument('uid')
        lat = self.get_argument('lat')
        lon = self.get_argument('lon')
        size = 20
        # part start with 0
        part = self.get_argument('part')
        prefix = Geohash.encode(lat, lon, get_geohash_precision_by_range(10000))
        ret = yield self.application.ground_center.get_actives_nearby(user_id, prefix, size * int(part), size)
        self.write_response(ret)


class GetTopicsHandler(CoroutineBaseHandler):
    @tornado.gen.coroutine
    def do_post(self):
        size = 20
        start = int(self.get_argument('start', 0))
        count = self.get_argument('count')
        result = yield self.application.ground_center.get_topic_list(start, size, count)
        self.write_response(result)

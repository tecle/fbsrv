# coding: utf-8
import logging
import time
import tornado.gen
import celeryapp.tasks as AsyncTasks

from model import (ActiveModel, CommentModel, TopicModel, UserModel)
from model.response import (Actives, Comments, Topics)
from utils.util_tools import datetime_to_timestamp


class SimpleCache(object):
    def __init__(self, data=None):
        self.data = data
        self.content_expire_at = None
        self.ssdata_expire_at = None


class GroundCenter(object):
    def __init__(self, ground_cache):
        self._ground_cache = ground_cache
        self._topic_cache = SimpleCache(Topics())
        self._topic_content_expire_time = 30 * 60
        self._topic_ssdata_expire_time = 30

    def _init_actives(self, user_id, rows, result):
        for row in rows:
            active_obj = result.actives.add()
            active_obj.activeId = row['id']
            active_obj.ownerId = row['uid']
            active_obj.topicId = row['tid']
            active_obj.content = row['content']
            active_obj.pictures = row['pics']
            active_obj.location = row['location']
            active_obj.publishTime = datetime_to_timestamp(row['create_time'])
            active_obj.nickName = row['nick_name']
            active_obj.avatar = row['avatar']
        self._ground_cache.get_actives_info(user_id, result)

    def _init_comments(self, comments, ret):
        for row in ret:
            comment_pb = comments.comments.add()
            comment_pb.commentId = row['id']
            comment_pb.activeId = row['aid']
            comment_pb.ownerId = row['uid']
            comment_pb.targetId = row['tid']
            comment_pb.targetUserId = row['tuid']
            comment_pb.ownerAvatar = row['avatar']
            comment_pb.ownerNickname = row['nick_name']
            comment_pb.content = row['content']
            comment_pb.targetNickname = row['snick']
            comment_pb.targetContent = row['scontent']
            comment_pb.publishTime = datetime_to_timestamp(row['create_time'])

    @tornado.gen.coroutine
    def get_actives_nearby(self, user_id, prefix, part, size):
        ret = yield tornado.gen.Task(ActiveModel.get_actives_by_range, prefix, size * int(part), size)
        result = None
        if ret:
            result = Actives()
            self._init_actives(user_id, ret, result)
        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def get_actives(self, user_id, topic_id, start_active_id, size, want_new=True):
        result = Actives()
        if want_new:
            ret = yield tornado.gen.Task(ActiveModel.get_latest_actives, topic_id, size)
        else:
            ret = yield tornado.gen.Task(ActiveModel.get_older_actives, topic_id, start_active_id, size)
        if ret:
            self._init_actives(user_id, ret, result)
        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def add_active(self, owner_id, topic_id, body, pics, location, lon, lat, geo_code):
        active_id = yield tornado.gen.Task(
            ActiveModel.insert, owner_id, topic_id, body, pics, location, lon, lat, geo_code)
        if active_id:
            self._ground_cache.process_add_active(topic_id, active_id, owner_id, lat, lon)
        raise tornado.gen.Return(active_id)

    @tornado.gen.coroutine
    def del_active(self, topic_id, active_id):
        success = yield tornado.gen.Task(ActiveModel.delete, active_id)
        if success:
            self._ground_cache.remove_active(topic_id, active_id)
        raise tornado.gen.Return(success)

    @tornado.gen.coroutine
    def add_comment(self, topic_id, active_id, owner_id, target_id, target_user_id, content, summary):
        cmt = CommentModel(aid=active_id, uid=owner_id, tid=target_id, tuid=target_user_id, content=content,
                           refer=summary)
        cmt_id = yield tornado.gen.Task(cmt.save)
        if cmt_id:
            self._ground_cache.process_add_comment(topic_id, active_id, owner_id)
            AsyncTasks.push_comment_message_to_user.apply_async(
                args=(target_user_id, owner_id, active_id, cmt_id, content, summary))
        raise tornado.gen.Return(cmt_id)

    @tornado.gen.coroutine
    def del_comment(self, active_id, comment_id):
        affect_rows = yield tornado.gen.Task(CommentModel.delete, comment_id)
        self._ground_cache.add_comment_number(active_id, -1)
        raise tornado.gen.Return(affect_rows is not None)

    @tornado.gen.coroutine
    def get_active_comments(self, active_id, offset, size):
        ret = yield tornado.gen.Task(CommentModel.select_some, active_id, offset, size)
        cmts = Comments()
        if ret:
            self._init_comments(cmts, ret)
        raise tornado.gen.Return(cmts)

    @tornado.gen.coroutine
    def get_topic_list(self, start, size, joined_count):
        result = Topics()
        # 话题内容过期，重新从数据库读取
        logging.debug('read topic from db.')
        rows = yield tornado.gen.Task(TopicModel.get_topics, start, size)
        for row in rows:
            tmp = result.topics.add()
            tmp.topicId = row['id']
            tmp.title = row['title']
            tmp.detail = row['detail']
            tmp.pics = row['pics']
        # 话题统计数据过期，重新更新统计数据(参与用户/参与人数/动态数等)
        avatar_data = self._ground_cache.process_topics_data(result.topics, joined_count)
        null_avatar = [key for key, val in avatar_data.iteritems() if not val]
        if null_avatar:
            avatars = yield tornado.gen.Task(UserModel.get_avatar, null_avatar)
            for uid, avatar in avatars.iteritems():
                avatar_data[str(uid)] = avatar
        for topic in result.topics:
            topic.participants = [avatar_data[key] for key in topic.participants]
        raise tornado.gen.Return(result)

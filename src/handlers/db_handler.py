# coding: utf-8

import json
import logging
import tornado.gen
import tornado.web
from model.response.coredata import RecommendUsers
from model.response.coredata import UserDetail
from model.response.coredata import UsersMetaInfo

from model.report import Report
from model.topic import Topic as TopicModel
from model.user_info import UserInfo
from model.response.grounddata import Topics


class HelloServiceHandler(tornado.web.RequestHandler):
    def post(self):
        self.write('HELLO')


class GetUsersAvatarHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        uid_list = self.get_argument('uid')
        if uid_list:
            logging.info('get users[{}] avatar from db.'.format(uid_list))
            ret = yield tornado.gen.Task(UserInfo.get_avatar, uid_list)
            if ret:
                self.write(json.dumps(ret))
            else:
                self.set_status(510, 'db error.')
        else:
            self.set_status(511, 'param error')


class GetRecommendUserFromDBHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        params = json.loads(self.request.body)
        offset = int(params["start"])
        size = int(params["size"])
        uid = params["uid"]
        sex = params.get("sex", None)
        star = params.get("star", None)
        result = RecommendUsers()
        yield tornado.gen.Task(
            UserInfo.get_recommend_users, result, uid, offset, size, gender=sex, star=star)
        result.success = True
        self.write(result.SerializeToString())


class UpdateUserHobbyToDBHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        uid = self.get_argument("uid")
        hobbies = int(self.get_argument('hobbies'))
        res = yield tornado.gen.Task(UserInfo.add_hobby, uid, hobbies)
        self.write('OK' if res is not None else 'FAIL')


class DeleteTopicFromDBHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        topic_id = self.get_argument('id')
        res = yield tornado.gen.Task(TopicModel.delete_topic, topic_id)
        self.write('FAIL' if res is None else 'OK')


class GetUserInfoFromDBHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        ids = self.get_argument('users')
        id_for_db = ids.split(',')
        users_pb = UsersMetaInfo()
        yield tornado.gen.Task(UserInfo.get_users_pb_info, id_for_db, users_pb)
        self.write(users_pb.SerializeToString())


class GetUserDetailFromDBHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        uid = self.get_argument('uid')
        user_pb = UserDetail()
        res = yield tornado.gen.Task(UserInfo.get_detail, uid, user_pb)
        self.write(user_pb.SerializeToString() if res else '')


class ReportHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        reporter_id = self.get_argument('rid')
        target_id = self.get_argument('tid')
        target_owner_id = self.get_argument('toid')
        report_type = self.get_argument('rt')
        Report.add(reporter_id, target_id, target_owner_id, report_type)


class CreateUserByWxHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        obj = json.loads(self.request.body)
        # open_id, union_id, device, refresh_token, refresh_token_time, nick_name, avatar
        user_id, already_exist, extra = yield tornado.gen.Task(
            UserInfo.wx_add_user,
            obj['opi'], obj['uni'], obj['dvc'], obj['rtk'], obj['rtt'], obj['nick'], obj['at']
        )
        # extra = (ban_st, avatar, sign, nick)
        self.write(json.dumps({
            'OK': True,
            'UID': user_id,
            'NEW': not already_exist,
            'BAN': extra[0],
            'AT': extra[1],
            'SN': extra[2],
            'NK': extra[3]
        }) if user_id else '{"OK":false}')


class LoginByWxHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        user_id = self.get_argument('uid')
        device = self.get_argument('dvc')
        success = yield tornado.gen.Task(UserInfo.wx_check_user, user_id, device)
        self.write('{"OK":true}' if success else '{"OK":false}')


class UpdateTokenByWxHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        user_id = self.get_argument('usr')
        token = self.get_argument('tkn')
        ctime = self.get_argument('t')
        success = yield tornado.gen.Task(UserInfo.wx_update_token, user_id, token, ctime)
        self.write('1' if success else '')

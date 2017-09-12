# coding: utf-8
import json
import logging

import tornado.gen
import tornado.web

from handlers.base_handler import KVBaseHandler
from model.tableconstant import USER_BANNED, USER_ALLOWED
from model.user_info import UserInfo
from model.cache.server_cache import ServerCache
from model.topic import Topic
from utils.subscriber import make_pub_message

door_key = 'KeyboardMan'


class AddHobbyPageHandler(KVBaseHandler):
    @tornado.web.asynchronous
    def post(self):
        hobby_id = int(self.get_argument('hid'))
        hobby_detail = self.get_argument('desc').strip()
        operation_type = int(self.get_argument('op_type'))

        if not 0 <= hobby_id < 64:
            self.write("Invalid hobby id.")
            self.finish()
            return
        if len(hobby_detail) == 0:
            self.write('Hobby description can not be empty.')
            self.finish()
            return
        if operation_type not in [0, 1]:
            self.write('invalid operation type')
            self.finish()
            return
        real_id = hobby_id
        server_cache = self.application.redis_wrapper.get_cache(ServerCache.cache_name)
        if operation_type:
            ret = server_cache.get_hobby(64)
            for item in ret:
                kv = item.split(':')
                if kv[0] == str(real_id) or kv[1] == hobby_detail:
                    logging.info('remove old hobby[%s]' % item)
                    server_cache.remove_hobby(item)
            server_cache.add_hobby(real_id, hobby_detail)
        else:
            server_cache.remove_hobby("%s:%s" % (real_id, hobby_detail))
        self.write('Done')
        self.finish()


class ShowHobbiesHandler(KVBaseHandler):
    @tornado.web.asynchronous
    def post(self):
        server_cache = self.application.redis_wrapper.get_cache(ServerCache.cache_name)
        ret = server_cache.get_hobby(64)
        self.write('<br/>'.join(sorted(['%s:%s' % (int(item.split(":")[0]), item.split(":")[1])
                                        for item in ret],
                                       cmp=lambda x, y: int(x.split(":")[0]) - int(y.split(":")[0]))))
        self.finish()

    def get_easy_id(self, real_id):
        count = 0
        while real_id > 1:
            real_id >>= 1
            count += 1
        return count


class AddTopicHandler(KVBaseHandler):
    @tornado.web.asynchronous
    def post(self):
        title = self.get_argument('title').strip()
        content = self.get_argument('desc').strip()
        pics = self.get_argument('pics').strip()
        visible = int(self.get_argument('visible')) > 0
        hobby_list = [int(item.strip()) for item in self.get_argument('hobbies').split(',') if item.strip()]
        hobbies = 0
        for item in hobby_list:
            if 0 <= item < 64:
                hobbies ^= (1 << item)
        if not title or not content:
            self.write('title or content must set.')
            self.finish()
            return
        id = Topic.insert(self.application.db_conn, title=title, detail=content, visible=visible, hobbies=hobbies,
                          pics=pics)
        self.write("add topic succsss, id is %s" % id)
        self.finish()


class QueryTopicHandler(KVBaseHandler):
    @tornado.web.asynchronous
    def post(self):
        tps = Topic.select_all(self.application.db_conn)
        self.write(json.dumps(tps, ensure_ascii=False, indent=2).replace('\n', '<br/>'))
        self.finish()


class UpdateTopicHandler(KVBaseHandler):
    @tornado.web.asynchronous
    def post(self):
        topic_id = self.get_argument('tid')
        title = self.get_argument('title')
        mtitle = self.get_argument('mtitle') == '1'
        content = self.get_argument('desc')
        mcontent = self.get_argument('mdesc') == '1'
        pics = self.get_argument('pics')
        mpics = self.get_argument('mpics') == '1'
        mhobbies = self.get_argument('hobbies') == '1'
        mweight = self.get_argument('mweight') == '1'
        weight = self.get_argument('weigh')
        hobby_list = None
        if mhobbies:
            hobby_list = [int(item.strip()) for item in self.get_argument('hobbies').split(',')]

        visible = int(self.get_argument('visible'))
        kwargs = {}
        if mtitle:
            kwargs['title'] = title
        if mcontent:
            kwargs['detail'] = content
        if mpics:
            kwargs['pics'] = pics
        if hobby_list:
            hobbies = 0
            for item in hobby_list:
                if 0 <= item < 64:
                    hobbies ^= (1 << item)
            kwargs['hobbies'] = hobbies
        if mweight:
            kwargs['weight'] = weight
        if visible > 0:
            kwargs['visible'] = visible < 2
        if not kwargs:
            self.write('nothing to update.')
            self.finish()
            return
        ar = Topic.update_topic(self.application.db_conn, topic_id, **kwargs)
        self.write("update topic succsss, affect rows %s" % ar)
        self.finish()


class SwitchRedisHandler(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        key = self.request.headers.get('DoorKey', None)
        if key != door_key:
            return
        host = self.get_argument('host')
        port = self.get_argument('port')
        db = self.get_argument('db', 0)
        pwd = self.get_argument('pwd', None)
        if self.application.redis_wrapper.reset_redis_server(host, port, db, pwd):
            self.write('switch success')
        else:
            self.write('switch failed.')


class OPBase(tornado.web.RequestHandler):
    def post(self):
        key = self.get_argument('DoorKey', None)
        if key != door_key:
            self.write('{"code": 400, "msg": "Invalid door key."}')
            return
        self.do_post()

    def do_post(self):
        raise NotImplementedError()


class CoroutineOPBase(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        key = self.get_argument('DoorKey', None)
        if key != door_key:
            self.write('{"code": 400, "msg": "Invalid door key."}')
            return
        yield self.do_post()

    @tornado.gen.coroutine
    def do_post(self):
        raise NotImplementedError()


class ChangeVersionHandler(OPBase):
    def do_post(self):
        cur_ver_code = int(self.get_argument('cvc'))
        cur_ver_str = self.get_argument('cvs').strip()
        cur_ver_info = self.get_argument('cvi').strip()
        min_ver_req = int(self.get_argument('mvr'))
        download_url = self.get_argument('dl').strip()

        for item in (cur_ver_code, cur_ver_str, cur_ver_info, min_ver_req, download_url):
            if not item:
                self.write('有字段为空.')
                return

        ver_obj = {
            "code": int(cur_ver_code),
            "text": cur_ver_str,
            "min": int(min_ver_req),
            "dl": download_url,
            "info": cur_ver_info
        }
        pub_obj = make_pub_message(self.application.app_conf.version_routing_key, ver_obj)

        received_num = self.application.get_cache(ServerCache.cache_name).set_app_version_info(
            json.dumps(ver_obj), json.dumps(pub_obj))
        if received_num < 1:
            self.write('{"code": 1, "msg": "no one received this change..."}')
        else:
            logging.info('%s guest has received this change.', received_num)
            self.write('{"code": 0, "msg": "ok"}')


class GetVersionHandler(OPBase):
    def do_post(self):
        res = self.application.get_cache(ServerCache.cache_name).get_app_version_info()
        self.write(json.dumps(res, indent=2, ensure_ascii=False).encode('utf-8'))


class GameFreezingHandler(OPBase):
    def do_post(self):
        op = self.get_argument('frz')
        games = [int(game) for game in self.get_argument('game').split(',')]
        game_cfg = self.application.game_manager.game_config
        game_manager = self.application.game_manager
        if op == '1':
            game_manager.freeze_games(set(games))
            for game in games:
                game_cfg.freeze_game(game)
        elif op == '0':
            game_manager.unfreeze_games(set(games))
            for game in games:
                game_cfg.unfreeze_game(game)
        self.write('{"code": 0, "msg": "ok"}')


class UserOperationHandler(CoroutineOPBase):
    @tornado.gen.coroutine
    def do_post(self):
        op = int(self.get_argument('op'))
        uid = self.get_argument('uid')
        uinf = UserInfo()
        uinf.user_id = uid
        uinf.ban_status = USER_BANNED if op == 0 else USER_ALLOWED
        self.write('{"st": "ok", "msg": null}')

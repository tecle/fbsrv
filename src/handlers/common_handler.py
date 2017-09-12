# coding: utf-8

import datetime
import logging
import os
import time

from model.cache import UserInfoCache

import celeryapp.tasks as CeleryTasks
from handlers.base_handler import KVBaseHandler
from model.cache.server_cache import ServerCache
from model.response import Status, HobbyList, RecommendUsers, QiNiuUploadData, QiNiuDownloadData, DataShell
from utils.common_define import ErrorCode, HttpErrorStatus
from utils.util_tools import validate_position_pair

valid_extensions = set(('.jpg', '.png', '.jpeg', '.gif'))


class Get7CowUploadCertificate(KVBaseHandler):
    def do_post(self):
        fs = self.get_argument('files').split(' ')
        uid = self.get_argument('uid')
        if fs:
            qiniu_pb = QiNiuUploadData()
            for f in fs:
                extension = os.path.splitext(f)[1]
                if extension not in valid_extensions:
                    logging.debug('invalid extension:{}'.format(extension))
                    qiniu_pb.success = False
                    qiniu_pb.err_code = ErrorCode.InvalidFileExtension
                    qiniu_pb.reset()
                    break
                file_name = '{0}_{1}{2}'.format(uid, int(time.time() * 1000000), extension)
                qiniu_pb.add_pair(f, file_name, self.application.qiniu_api.get_upload_url(file_name))
            self.write_response(qiniu_pb)
        else:
            self.set_status(*HttpErrorStatus.WrongParams)
        self.finish()


class Get7CowDownloadCertificate(KVBaseHandler):
    def do_post(self):
        fs = self.get_argument('files')
        qiniu_pb = QiNiuDownloadData()
        for meta in fs:
            style = meta.get('size', None)
            qiniu_pb.add_url(self.application.qiniu_api.get_download_url(meta['bkt'], meta['name'], style))
        self.write_response(qiniu_pb)
        self.finish()


class ReportHandler(KVBaseHandler):
    def do_post(self):
        reporter_id = self.get_argument('uid')
        target_id = self.get_argument('tid')
        target_owner_id = self.get_argument('oid')
        report_type = self.get_argument('type')
        CeleryTasks.add_report.apply_async(args=(
            reporter_id, target_id, target_owner_id, report_type
        ))
        # self.application.async_db.report(reporter_id, target_id, target_owner_id, report_type, None)
        result = Status()
        result.success = True
        self.write_response(result)
        self.finish()


class SuggestionHandler(KVBaseHandler):
    def do_post(self):
        type = self.get_argument('type')
        args = (
            self.get_argument('uid'),
            self.get_argument('nick'),
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            self.get_argument('device'),
            self.get_argument('android'),
            self.get_argument('code'),
            self.get_argument('net'),
            self.get_argument('content')
        )
        if type == 'S':
            CeleryTasks.opinion_feedback.apply_async(args=args)
        elif type == 'C':
            CeleryTasks.consult.apply_async(args=args)
        # self.application.async_db.add_suggest(self.get_argument('uid'), self.get_argument('msg'), None)
        status = Status()
        self.write_response(status)
        self.finish()


class GetAllHobbiesHandle(KVBaseHandler):
    def do_post(self):
        result = HobbyList()
        result.status.success = True
        hbs = self.application.redis_wrapper.get_cache(ServerCache.cache_name).get_all_hobbies()
        for item in hbs:
            result.data.append(item)
        self.write_response(result)
        self.finish()


class GetHobby(GetAllHobbiesHandle):
    def do_post(self):
        size_str = self.get_argument("size")

        result = HobbyList()
        result.status.success = True
        size = int(size_str)

        items = self.application.redis_wrapper.get_cache(ServerCache.cache_name).get_hobby(size)
        for item in items:
            result.data.append(item)
        self.write_response(result)
        self.finish()


class GetRecommendUsersHandler(KVBaseHandler):
    SEX_STRINGS = ['1', '0', None]

    def do_post(self):
        self.application.async_db.get_recommend_user(self.request.body, self.on_finish_get_recommend_user)

    def on_finish_get_recommend_user(self, resp):
        result = RecommendUsers()
        if not resp.error:
            result.ParseFromString(resp.body)
            result.success = True
            self.application.redis_wrapper.get_cache(UserInfoCache.cache_name).get_recommend_users(result)
            for user in result.users:
                user.avatar = self.application.qiniu_api.get_pub_url(user.avatar)
        else:
            result.success = False
            result.code = ErrorCode.ServerError
        self.write_response(result)
        self.finish()


class ReportHeartbeatHandler(KVBaseHandler):
    def do_post(self):
        status = self.get_argument('st')
        uid = self.get_argument('uid')
        longitude = self.get_argument('lon')
        latitude = self.get_argument('lat')
        panel = self.get_argument('panel')
        data = self.get_argument('data')
        timestamp = self.get_argument('ts')
        site = self.get_argument('site')

        result = Status()
        result.success = True
        if validate_position_pair(longitude, latitude):
            self.application.redis_wrapper.get_cache(UserInfoCache.cache_name).update_user_heartbeat(
                status, panel, data, uid, timestamp, site, longitude, latitude, 5)
        else:
            result.success = False
            result.code = ErrorCode.InvalidLocationPair
        self.write_response(result)
        self.finish()


class UpdateUserToken(KVBaseHandler):
    def do_post(self):
        uid = self.get_argument('uid')
        self.application.async_im.refresh_token(uid, self.on_finish_update)

    def on_finish_update(self, resp):
        result = ""
        if resp:
            result = resp['info']['token']
        self.write_response(result)
        self.finish()


class GetAppVersionInfoHandler(KVBaseHandler):
    def do_post(self):
        self.write(str(self.application.app_conf))
        self.finish()


class GetCargoConfHandler(KVBaseHandler):
    def do_post(self):
        ds = DataShell()
        ds.data = self.application.cargo_conf.data
        self.write_response(ds)
        self.finish()

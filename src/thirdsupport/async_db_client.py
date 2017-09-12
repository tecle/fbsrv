# coding: utf-8
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPClient
from tornado.httpclient import HTTPRequest
import urllib
import urllib2
import logging
import time
import json


class AsyncDBClient(object):
    def __init__(self, host):
        self.host = 'http://%s%%s' % host
        db_table = (
            (r'/db/user/addhobby', 'UpdateUserHobbyToDBHandler'),
            (r'/db/user/updatetoken', 'MapUserTokenToDBHandler'),
            (r'/db/user/detail', 'GetUserDetailFromDBHandler'),
            (r'/db/user/getsome', 'GetUserInfoFromDBHandler'),
            (r'/db/user/recommend', 'GetRecommendUserFromDBHandler'),
            (r'/db/hello', 'HelloServiceHandler'),
            (r'/db/user/avatar', 'GetUsersAvatarHandler'),
            (r'/db/wx/new', 'CreateUserByWxHandler'),
            (r'/db/wx/login', 'LoginByWxHandler'),
            (r'/db/wx/update', 'UpdateTokenByWxHandler')
        )
        for pair in db_table:
            setattr(self, "%s%s" % (pair[1].replace('Handler', ''), 'Url'), self.host % pair[0])

    def check_db_server(self):
        client = HTTPClient()
        stable_count = 0
        for i in range(10):
            req = HTTPRequest(self.HelloServiceUrl, method='POST', body='')
            rsp = client.fetch(req)
            if rsp.error or rsp.body != 'HELLO':
                logging.warning('Say hello to db server[{}] failed.'.format(self.HelloServiceUrl))
                time.sleep(i << 1)
                continue
            stable_count += 1
            time.sleep(0.01)
        client.close()
        return stable_count / 10.0

    def easy_request(self, url, body="", callback=None):
        req = HTTPRequest(url=url, body=body, method='POST')
        AsyncHTTPClient().fetch(req, callback)

    def add_hobby_to_user(self, uid, hobbies, callback):
        url = '%s?uid=%s&hobbies=%s' % (self.UpdateUserHobbyToDBUrl, uid, hobbies)
        req = HTTPRequest(url=url, body="", method='POST')
        AsyncHTTPClient().fetch(req, callback)

    def get_user_detail(self, user_id, callback):
        url = '%s?uid=%s' % (self.GetUserDetailFromDBUrl, user_id)
        self.easy_request(url, callback=callback)

    def get_user_info_by_list(self, user_list, callback):
        url = '%s?users=%s' % (self.GetUserInfoFromDBUrl, urllib2.quote(','.join(user_list)))
        self.easy_request(url, callback=callback)

    def get_recommend_user(self, origin_params, callback):
        self.easy_request(self.GetRecommendUserFromDBUrl, body=origin_params, callback=callback)

    def get_user_avatar(self, uid_list, callback):
        self.easy_request(
            '{}?uid={}'.format(self.GetUsersAvatarUrl, urllib.quote(','.join(uid_list))), callback=callback)

    def add_wx_user(self, openid, unionid, device, refresh_token, token_time, nick_name, avatar, callback):
        self.easy_request(self.CreateUserByWxUrl, body=json.dumps({
            'opi': openid,
            'uni': unionid,
            'dvc': device,
            'rtk': refresh_token,
            'rtt': token_time,
            'nick': nick_name,
            'at': avatar
        }), callback=callback)

    def check_wx_login(self, user_id, device, callback):
        self.easy_request(
            '{}?uid={}&dvc={}'.format(self.LoginByWxUrl, user_id, device), callback=callback)

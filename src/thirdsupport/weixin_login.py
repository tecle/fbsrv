# coding: utf-8


import re
import json
import time
import urllib
import logging
from collections import namedtuple
from functools import wraps
import tornado.gen
from tornado.httpclient import HTTPRequest, AsyncHTTPClient

TokenInfo = namedtuple('TokenInfo', ('access_token', 'expire_in', 'refresh_token', 'openid', 'time'))
WeiXinUserInfo = namedtuple('WeiXinUserInfo', (
    'openid', 'nickname', 'sex', 'province', 'city', 'country', 'headimgurl', 'unionid'))
QQUserInfo = namedtuple('QQUserInfo', ('nickname', 'headimgurl'))


def http_response(func):
    @wraps(func)
    def func_(resp):
        if resp.error:
            logging.warning('{} failed: {}'.format(func.__name__, resp.body))
            return None
        try:
            return func(resp.body)
        except Exception, e:
            logging.exception('Execute {} failed with body:{}'.format(func.__name__, resp.body))
            return None

    return func_


qq_openid_ptn = re.compile(r'callback\((.*?)\);')


class WeiXinLoginTool(object):
    def __init__(self, wx_app_id, wx_secret, wx_domain):
        self.wechat_app_id = wx_app_id
        self.wechat_secret = wx_secret
        self.wechat_api_domain = wx_domain
        self.qq_app_id = None
        self.qq_app_key = None
        self.qq_api_domain = 'https://graph.qq.com'

    def get_qq_access_token_request(self, code, redirect_url):
        params = {
            'grant_type': 'authorization_code',
            'client_id': self.qq_app_id,
            'client_secret': self.qq_app_key,
            'code': code,
            'redirect_uri': redirect_url
        }
        return HTTPRequest(url='{}/oauth2.0/token?{}'.format(
            self.qq_api_domain, urllib.urlencode(params)))

    def get_qq_open_id_request(self, access_token):
        return HTTPRequest(url='{}/oauth2.0/me?access_token={}'.format(self.qq_api_domain, access_token))

    def get_qq_user_info_request(self, access_token, open_id):
        return HTTPRequest(url='{}/user/get_user_info?access_token={}&oauth_consumer_key={}&openid={}'.format(
            self.qq_api_domain, access_token, self.qq_app_id, open_id
        ))

    @staticmethod
    @http_response
    def parse_get_qq_access_token_response(body):
        ary = body.split('&')
        params = {}
        for s_pair in ary:
            key, val = s_pair.split('=')
            params[key] = val
        return TokenInfo(
            access_token=params['access_token'], expire_in=params['expires_in'],
            refresh_token=params['refresh_token'], openid='', time=int(time.time())
        )

    @staticmethod
    @http_response
    def parse_get_qq_open_id_response(body):
        content = qq_openid_ptn.findall(body)
        if content:
            obj = json.loads(content[0])
            return obj['openid']
        logging.warning('cannot find openid msg in body:{}'.format(body))
        return None

    @staticmethod
    @http_response
    def parse_get_user_info_response(body):
        obj = json.loads(body)
        if obj['ret'] < 0:
            logging.warning('get user info from qq failed. reason:{}'.format(obj['msg']))
            return None
        return QQUserInfo(nickname=obj['nickname'], headimgurl=obj['figureurl_qq_1'])


    ''' wechat part '''
    @tornado.gen.coroutine
    def get_wx_access_token(self, code):
        params = {
            'appid': self.wechat_app_id,
            'secret': self.wechat_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }
        request = HTTPRequest(url='{}/sns/oauth2/access_token?{}'.format(
            self.wechat_api_domain, urllib.urlencode(params)))
        response = yield AsyncHTTPClient().fetch(request)
        token_info = self.parse_get_wx_access_token_response(response)
        raise tornado.gen.Return(token_info)

    def refresh_token_request(self, refresh_token):
        '''use parse_get_wx_access_token_response to parse response'''
        params = {
            'appid': self.wechat_app_id,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        return HTTPRequest(url='{}/sns/oauth2/refresh_token?{}'.format(
            self.wechat_api_domain, urllib.urlencode(params)))

    def check_token_status_request(self, access_token, open_id):
        params = {
            'access_token': access_token,
            'open_id': open_id
        }
        return HTTPRequest(url='{}/sns/auth?{}'.format(
            self.wechat_api_domain, urllib.urlencode(params)))

    @staticmethod
    @http_response
    def parse_get_wx_access_token_response(body):
        obj = json.loads(body)
        if 'errcode' in obj:
            logging.warning('get access token failed:{0},{1}'.format(obj['errcode'], obj['errmsg']))
            return None
        return TokenInfo(
            access_token=obj['access_token'], expire_in=obj['expires_in'],
            refresh_token=obj['refresh_token'], openid=obj['openid'], time=int(time.time())
        )

    @staticmethod
    @http_response
    def parse_check_token_status_response(body):
        obj = json.loads(body)
        if 'errcode' not in obj:
            logging.warning('get access token status failed:{0}-{1}'.format(obj['errcode'], obj['errmsg']))
            return None
        return obj['errcode'] == 0

    @tornado.gen.coroutine
    def get_wx_user_info(self, access_token, openid):
        params = {
            'access_token': access_token,
            'openid': openid
        }
        request = HTTPRequest(url='{}/sns/userinfo?{}'.format(
            self.wechat_api_domain, urllib.urlencode(params)))
        response = yield AsyncHTTPClient().fetch(request)
        uinfo = self.parse_get_wx_user_info_response(response)
        raise tornado.gen.Return(uinfo)

    @staticmethod
    @http_response
    def parse_get_wx_user_info_response(body):
        obj = json.loads(body)
        if 'errcode' in obj:
            logging.warning('get access token failed:{0}-{1}'.format(obj['errcode'], obj['errmsg']))
            return None
        return WeiXinUserInfo(
            openid=obj['openid'], nickname=obj['nickname'],
            sex=obj['sex'], province=obj['province'], city=obj['city'], country=obj['country'],
            headimgurl=obj['headimgurl'], unionid=obj.get('unionid', '')
        )

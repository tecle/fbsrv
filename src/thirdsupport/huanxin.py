# coding: utf-8
from tornado.httpclient import HTTPRequest
import json
import logging


class HuanXinAPI(object):
    def __init__(self, org_name, app_name, client_id, client_secret, host):
        self.ORG_NAME = org_name
        self.APP_NAME = app_name
        self.CLIENT_ID = client_id
        self.CLIENT_SECRET = client_secret
        self.HOST = host

        self.token_url = "%s/%s/%s/token" % (self.HOST, self.ORG_NAME, self.APP_NAME)
        self.register_url = "%s/%s/%s/users" % (self.HOST, self.ORG_NAME, self.APP_NAME)
        self.push_msg_url = "%s/%s/%s/messages" % (self.HOST, self.ORG_NAME, self.APP_NAME)

        self.token_body = '{"grant_type": "client_credentials","client_id": "%s","client_secret": "%s"}' % \
                          (self.CLIENT_ID, self.CLIENT_SECRET)
        self.push_msg_body_tpl = '{"target_type":"users", "targe":["%s"], "msg":{"type":"%s", "action":"%s"}}'

        self.common_headers = [("Content-Type", "application/json")]
        self.token = None
        self.token_alive_time = None

    def make_token_request(self):
        return HTTPRequest(url=self.token_url, body=self.token_body, headers=self.common_headers, method='POST')

    def make_register_request(self, user_name, user_password, user_nick):
        headers = self.common_headers + [("Authorization", "Bearer %s" % self.token)]
        logging.debug('headers:%s' % headers)
        body = '{"username":"%s","password":"%s", "nickname":"%s"}' % (user_name, user_password, user_nick)
        return HTTPRequest(url=self.register_url, body=body, headers=headers, method='POST')

    def make_push_msg_request(self, target_user, msg_type, msg_action):
        headers = self.common_headers + [("Authorization", "Bearer %s" % self.token)]
        logging.debug('push msg %s->%s' % (msg_type, msg_action))
        body = self.push_msg_body_tpl % (target_user, msg_type, msg_action)
        return HTTPRequest(url=self.push_msg_url, body=body, headers=headers, method='POST')

    def parse_token_response(self, resp):
        self.token = None
        if resp.code != 200:
            logging.error('get huanxin token failed.body:[%s]' % resp.body)
            return
        try:
            obj = json.loads(resp.body)
            self.token = obj['access_token']
            self.token_alive_time = obj['expires_in']
            logging.info('get HuanXin token[%s], expires in[%s]' % (self.token, self.token_alive_time))
        except Exception:
            logging.exception('Parse json result[%s] from huanxin failed.' % resp.body)
            return

    @staticmethod
    def parse_register_response(response):
        '''code = 401 means token invalid'''
        if response.code != 200:
            logging.warning('Receive bad status from huanxin:code[%s], body[%s]' % (response.code, response.body))
            return None, None
        user_id = None
        huanxin_id = None
        try:
            obj = json.loads(response.body)
            user_id = obj['entities'][0]['username']
            huanxin_id = obj['entities'][0]['uuid']
        except Exception:
            logging.exception('Parse json result[%s] from huanxin failed.' % response.body)
        return user_id, huanxin_id

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
            (r'/db/user/updatetoken', 'MapUserTokenToDBHandler'),
            (r'/db/user/getsome', 'GetUserInfoFromDBHandler'),
            (r'/db/hello', 'HelloServiceHandler'),
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

    def get_user_info_by_list(self, user_list, callback):
        url = '%s?users=%s' % (self.GetUserInfoFromDBUrl, urllib2.quote(','.join(user_list)))
        self.easy_request(url, callback=callback)

